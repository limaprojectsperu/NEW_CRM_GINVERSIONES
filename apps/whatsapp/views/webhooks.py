import requests
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes
from apps.redes_sociales.models import MessengerPlantilla
from ...utils.pusher_client import pusher_client
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.datetime_func import get_date_time, get_naive_peru_time
from apps.utils.tokens_phone import get_user_tokens_by_permissions
from apps.openai.openai_chatbot import ChatbotService
from django.test import RequestFactory
from rest_framework.request import Request
from ..views.whatsapp_app import WhatsappSendAPIView
import json
from rest_framework.parsers import JSONParser

chatbot = ChatbotService()

class WhatsappWebhookAPIView(APIView):
    """
    GET  /api/web-hooks/app    -> verifica token y responde hub_challenge
    POST /api/web-hooks/app   -> recibe mensajes de WhatsApp y guarda en BD
    """
    def get(self, request):
        hub_challenge   = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        hub_mode        = request.GET.get('hub.mode', '')

        setting = WhatsappConfiguracion.objects.filter(
            Estado=1
        ).first()

        if hub_mode == 'subscribe' and setting and setting.TokenHook == hub_verify_token:
            return HttpResponse(hub_challenge)
        return HttpResponseForbidden()

    def post(self, request):
        payload = request.data
        if not payload:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self._init_chat(payload)
        return Response({'status': 'ok'})

    def _init_chat(self, payload):
        entry   = payload.get('entry', [])[0]
        change  = entry.get('changes', [])[0]['value']
        # Datos según la carga de WhatsApp
        phone_admin = change['metadata']['display_phone_number']
        phone       = change['messages'][0]['from']
        message     = change['messages'][0]['text']['body']
        name        = change['contacts'][0]['profile']['name']
        newChat     = False

        # Obtener configuración por número de WhatsApp
        setting = WhatsappConfiguracion.objects.filter(
            Telefono=phone_admin
        ).first()

        # Crear o actualizar el chat
        chat = Whatsapp.objects.filter(
            IDRedSocial=setting.IDRedSocial,
            Telefono=phone
        ).first()

        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes+1
            chat.save()
        else:
            chat = Whatsapp.objects.create(
                IDRedSocial          = setting.IDRedSocial,
                Nombre               = name if name else phone,
                Telefono             = phone,
                IDEL                 = 1,
                nuevos_mensajes      = 1,
                Estado               = 1
            )
            newChat = True

            #push notification
            firebase_service = FirebaseServiceV1()
            tokens = get_user_tokens_by_permissions("whatsapp.index")
            if len(tokens) > 0:
                firebase_service.send_to_multiple_devices(
                    tokens=tokens,
                    title="Nuevo mensaje en WhatsApp",
                    body=message,
                    data={'type': 'router', 'route_name': 'WhatsappPage'}
                )

        # Fechas en formato local Perú
        Fecha, Hora = get_date_time()

        # Guardar mensaje entrante (Estado 2 = recibido)
        WhatsappMensajes.objects.create(
            IDChat   = chat.IDChat,
            Telefono = phone,
            Mensaje  = message,
            Fecha    = Fecha,
            Hora     = Hora,
            Estado   = 2
        )

        # Actualizar timestamps del chat
        dateNative = get_naive_peru_time()
        chat.FechaUltimaPlantilla = dateNative
        chat.updated_at           = dateNative 
        chat.save()

        # Marcar como vistos los mensajes anteriores
        WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)

        #respuesta automatica
        if newChat:
            template = MessengerPlantilla.objects.filter(marca_id=setting.marca_id, estado=True, tipo=1).first()
            if template:
                self.send_message(setting, chat, template.mensaje)
        
        #open AI
        if setting.openai and chat.openai:
            self.open_ai_response(setting, chat)
        
        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 'IDRedSocial': setting.IDRedSocial })
    
    def open_ai_response(self, setting, chat):
        ultimos_mensajes = list(WhatsappMensajes.objects.order_by('-IDChatMensaje')[:4])
        ultimos_mensajes.reverse()
        
        messages = []
        
        for entry in ultimos_mensajes:
            # Si Telefono coincide con el admin, es rol 'assistant'; si no, es 'user'
            role = "assistant" if entry.Telefono == setting.Telefono else "user"
            messages.append({"role": role, "content": entry.Mensaje})
        
        res = chatbot.get_response(setting.marca_id, messages)
        self.send_message(setting, chat, res, 2)

    def send_message(self, setting, chat, mensaje, origen = 1):
        Fecha, Hora = get_date_time()

        # 1. Prepara los datos que necesitas enviar
        message_data = {
            "IDRedSocial": setting.IDRedSocial,
            "tokenHook": setting.TokenHook,  
            "phone": chat.Telefono,
            "IDChat": chat.IDChat,
            "Telefono": setting.Telefono,
            "Mensaje": mensaje,
            "Fecha": Fecha,
            "Hora": Hora,
            "origen": origen,
        }
        
        # Crear una request factory
        factory = RequestFactory()
        # Crear WSGIRequest con JSON data
        django_request = factory.post(
            '/api/messenger-app/send-message/',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        # Convertir a DRF Request con parser específico
        drf_request = Request(django_request, parsers=[JSONParser()])
        # Llamar directamente a la vista
        view = WhatsappSendAPIView()
        response = view.post(drf_request)
        
        return response