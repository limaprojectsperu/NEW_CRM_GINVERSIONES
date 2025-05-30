import requests
from django.conf import settings
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, HttpResponseForbidden
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion
from apps.redes_sociales.models import MessengerPlantilla
from ...utils.pusher_client import pusher_client
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.datetime_func  import get_naive_peru_time, get_date_tiem
from apps.utils.tokens_phone import get_user_tokens_by_permissions
from apps.openai.openai_chatbot import ChatbotService

chatbot = ChatbotService()

class WebhookVerifyReceive(APIView):
    """
    GET /api/webhooks-messenger/app/{IDRedSocial}/
    Verifica el token de Facebook y devuelve hub_challenge.
    """
    def get(self, request, IDRedSocial):
        # Obtener todos los parámetros según la documentación
        hub_mode = request.GET.get('hub.mode', '')
        hub_challenge = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        
        # Obtener la configuración del token
        setting = MessengerConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()
        
        # Verificar modo y token como en la documentación
        if hub_mode and hub_verify_token:
            if hub_mode == 'subscribe' and setting and setting.TokenHook == hub_verify_token:
                # Responder con el challenge tal como se recibió
                return HttpResponse(hub_challenge)
            else:
                # Responder con 403 Forbidden si los tokens no coinciden
                return HttpResponseForbidden()
        
        # Si no hay modo o token, responder con 403
        return HttpResponseForbidden()

    """
    POST /api/webhooks-messenger/app/{IDRedSocial}/
    Recibe la carga útil JSON de Facebook en webhook.
    """
    def post(self, request, IDRedSocial):
        payload = request.data
        if not payload:
            return Response(status=status.HTTP_400_BAD_REQUEST)
 
        self._init_chat(payload, IDRedSocial)
        pusher_client.trigger('py-messenger-channel', 'PyMessengerEvent', { 'IDRedSocial': IDRedSocial })
        return Response({'status': 'ok'})

    def _get_user_name(self, sender_id, token):
        """
        Reemplaza la llamada curl a /{sender_id}?fields=name
        """
        url = f"https://graph.facebook.com/{sender_id}"
        try:
            resp = requests.get(url, params={
                'fields': 'name',
                'access_token': token
            }, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                # Retorna el nombre si existe, sino 'Usuario desconocido'
                return data.get('name', 'Usuario desconocido')
            else:
                return 'Usuario desconocido'
        except (requests.RequestException, ValueError):
            # Manejo de errores de conexión o JSON inválido
            return 'Usuario desconocido'


    def _init_chat(self, payload, IDRedSocial):
        """
        Lógica para crear/actualizar chat y guardar mensaje entrante.
        """
        entry = payload.get('entry', [])[0]
        msg   = entry.get('messaging', [])[0]

        sender_admin = msg['recipient']['id']
        sender_id    = msg['sender']['id']
        text         = msg.get('message', {}).get('text', '')
        newChat = False

        # Cargamos configuración
        setting = MessengerConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()

        # Buscamos chat existente
        chat = Messenger.objects.filter(
            IDRedSocial=IDRedSocial,
            IDSender=sender_id
        ).first()

        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes+1
            chat.save()
            user_name = chat.Nombre
        else:
            # Obtener nombre de usuario desde la API
            user_name = self._get_user_name(sender_id, setting.Token)
            chat = Messenger.objects.create(
                IDRedSocial=IDRedSocial,
                IDSender=sender_id,
                IDEL=1,
                Nombre=user_name,
                nuevos_mensajes=1,
                Estado=1
            )
            newChat = True

            #push notification
            firebase_service = FirebaseServiceV1()
            tokens = get_user_tokens_by_permissions("messenger.index")
            if len(tokens) > 0:
                firebase_service.send_to_multiple_devices(
                    tokens=tokens,
                    title="Nuevo mensaje en Messenger",
                    body=text,
                    data={'type': 'router', 'route_name': 'MessengerPage'}
                )
        
        # Fechas en español
        Fecha, Hora = get_date_tiem()

        # Guardar el nuevo mensaje (Estado 2 = recibido)
        new_msg = MessengerMensaje.objects.create(
            IDChat    = chat.IDChat,
            IDSender  = sender_id,
            Mensaje   = text,
            Fecha     = Fecha,
            Hora      = Hora,
            Estado    = 2
        )

        # Actualizar chat
        user_name = user_name or 'Usuario desconocido'  # Esto cubre None y string vacío
        if user_name == 'Usuario desconocido':
            nombreChat = f'Usuario desconocido {chat.IDChat}'
        else:
            nombreChat = user_name

        chat.Nombre  = nombreChat
        chat.updated_at = get_naive_peru_time()
        chat.save()

        # Marcar como vistos todos los anteriores con Estado=1
        MessengerMensaje.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)

        #respuesta automatica
        if newChat:
            template = MessengerPlantilla.objects.filter(marca_id=setting.marca_id, estado=True, tipo=1).first()
    
            if template:
                self.send_message(setting, chat, template)

    def send_message(self, setting, chat, template):
        if settings.DEBUG:
            url = settings.BASE_URL_LOCAL + "api/messenger-app/send-message"
        else:
            url = settings.BASE_URL_PRODUCTION + "api/messenger-app/send-message"

        Fecha, Hora = get_date_tiem()

        # 1. Prepara los datos que necesitas enviar
        message_data = {
            "IDRedSocial": setting.IDRedSocial,
            "tokenHook": setting.TokenHook,  
            "IdRecipient": chat.IDSender,
            "IDChat": chat.IDChat,
            "IDSender": setting.IDSender,
            "Mensaje": template.mensaje,
            "Fecha": Fecha,
            "Hora": Hora,
        }

        requests.post(url, json=message_data, timeout=10)
