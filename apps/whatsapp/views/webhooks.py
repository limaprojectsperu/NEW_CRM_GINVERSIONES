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
from apps.utils.find_states import find_state_id

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

        try:
            # Agregar logging para debug
            print(f"Payload recibido: {json.dumps(payload, indent=2)}")
            self._init_chat(payload)
        except (KeyError, IndexError) as e:
            print(f"Error al procesar el payload de WhatsApp: {e}")
            return Response({'status': 'error processing payload but acknowledged'})

        return Response({'status': 'ok'})

    def _init_chat(self, payload):
        entry   = payload.get('entry', [])[0]
        change  = entry.get('changes', [])[0]['value']

        # Verificar si hay mensajes o si es una actualización de estado
        if 'messages' not in change:
            print("No hay mensajes en el payload")
            return 

        message_obj = change['messages'][0]
        message_type = message_obj.get('type')
        
        print(f"Tipo de mensaje: {message_type}")
        print(f"Mensaje completo: {json.dumps(message_obj, indent=2)}")

        message_content = ""
        button_id = None
        
        # Manejo mejorado de respuestas interactivas
        if message_type == 'interactive':
            interactive = message_obj.get('interactive', {})
            print(f"Contenido interactivo: {json.dumps(interactive, indent=2)}")
            
            # Verificar si es respuesta de botón
            if 'button_reply' in interactive:
                button_reply = interactive['button_reply']
                message_content = button_reply.get('title', '')
                button_id = button_reply.get('id', '')
                print(f"Botón presionado - ID: {button_id}, Título: {message_content}")
            
            # Verificar si es respuesta de lista
            elif 'list_reply' in interactive:
                list_reply = interactive['list_reply']
                message_content = list_reply.get('title', '')
                button_id = list_reply.get('id', '')
                print(f"Lista seleccionada - ID: {button_id}, Título: {message_content}")
            
            else:
                print("Mensaje interactivo no reconocido")
                return

        elif message_type == 'text':
            message_content = message_obj['text']['body']
            print(f"Mensaje de texto: {message_content}")
        
        else:
            print(f"Tipo de mensaje no soportado: {message_type}")
            return

        # Validar que tenemos contenido del mensaje
        if not message_content:
            print("No se pudo extraer el contenido del mensaje")
            return

        # Datos según la carga de WhatsApp
        phone_admin = change['metadata']['display_phone_number']
        phone       = message_obj['from']
        
        # Obtener nombre del contacto (puede no estar presente)
        contacts = change.get('contacts', [])
        name = phone  # Por defecto usar el teléfono
        if contacts and len(contacts) > 0:
            profile = contacts[0].get('profile', {})
            name = profile.get('name', phone)

        # Obtener configuración por número de WhatsApp
        setting = WhatsappConfiguracion.objects.filter(
            Telefono=phone_admin
        ).first()

        if not setting:
            print(f"No se encontró configuración para el teléfono: {phone_admin}")
            return 

        # Crear o actualizar el chat
        chat = Whatsapp.objects.filter(
            IDRedSocial=setting.IDRedSocial,
            Telefono=phone
        ).first()

        newChat = False

        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes + 1
            chat.save()
        else:
            chat = Whatsapp.objects.create(
                IDRedSocial          = setting.IDRedSocial,
                Nombre               = name,
                Telefono             = phone,
                IDEL                 = find_state_id(2, 'No leído'),
                nuevos_mensajes      = 1,
                Estado               = 1
            )
            newChat = True

            # Push notification
            firebase_service = FirebaseServiceV1()
            tokens = get_user_tokens_by_permissions("messenger.index")
            if len(tokens) > 0:
                firebase_service.send_to_multiple_devices(
                    tokens=tokens,
                    title="Nuevo mensaje en WhatsApp",
                    body=message_content,
                    data={'type': 'router', 'route_name': 'WhatsappPage'}
                )

        # Fechas en formato local Perú
        Fecha, Hora = get_date_time()

        # Guardar mensaje entrante (Estado 2 = recibido)
        mensaje_guardado = WhatsappMensajes.objects.create(
            IDChat   = chat.IDChat,
            Telefono = phone,
            Mensaje  = message_content,
            Fecha    = Fecha,
            Hora     = Hora,
            Estado   = 2
        )

        # Si es respuesta de botón, guardar información adicional
        if button_id:
            # Aquí puedes agregar lógica específica para manejar diferentes botones
            print(f"Procesando respuesta de botón: {button_id}")

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

        # Respuesta automática
        if newChat:
            template = MessengerPlantilla.objects.filter(
                marca_id=setting.marca_id, 
                estado=True, 
                tipo=1
            ).first()
            if template:
                self.send_message(setting, chat, template.mensaje)

        # OpenAI
        if setting.openai and chat.openai:
            self.open_ai_response(setting, chat)

        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 'IDRedSocial': setting.IDRedSocial })
        

    def open_ai_response(self, setting, chat):
        ultimos_mensajes = list(WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat
        ).order_by('-IDChatMensaje')[:4])
        ultimos_mensajes.reverse()
        
        messages = []
        
        for entry in ultimos_mensajes:
            role = "assistant" if entry.Telefono == setting.Telefono else "user"
            messages.append({"role": role, "content": entry.Mensaje})
        
        res = chatbot.get_response(setting.marca_id, messages)
        self.send_message(setting, chat, res, 2)

    def send_message(self, setting, chat, mensaje, origen=1):
        Fecha, Hora = get_date_time()

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
        
        factory = RequestFactory()
        django_request = factory.post(
            '/api/messenger-app/send-message/',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        drf_request = Request(django_request, parsers=[JSONParser()])
        view = WhatsappSendAPIView()
        response = view.post(drf_request)
        
        return response