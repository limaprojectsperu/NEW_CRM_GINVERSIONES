import locale
import requests
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, HttpResponseForbidden
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion
from ...utils.pusher_client import pusher_client

# Aseguramos formato en español para meses
#try:
    #locale.setlocale(locale.LC_TIME, 'es_PE.UTF-8')
#except locale.Error:
    # Dependiendo del servidor puede variar el locale; ajuste según necesite
    #locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')


class WebhookVerifyReceive(APIView):
    """
    GET /api/webhooks-messenger/app/{IDRedSocial}/
    Verifica el token de Facebook y devuelve hub_challenge.
    """
    def get(self, request, IDRedSocial):
        # Usar los nombres correctos de los parámetros
        hub_challenge = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        
        setting = MessengerConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()
        
        if setting and setting.TokenHook == hub_verify_token:
            # Retornar SOLO el hub_challenge sin formateo adicional
            return HttpResponse(hub_challenge)
        
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
        pusher_client.trigger('py-messenger-channel', 'PyMessengerEvent', {})
        return Response({'status': 'ok'})


    def _get_user_name(self, sender_id, token):
        """
        Reemplaza la llamada curl a /{sender_id}?fields=name
        """
        url = f"https://graph.facebook.com/{sender_id}"
        resp = requests.get(url, params={
            'fields': 'name',
            'access_token': token
        })
        data = resp.json()
        return data.get('name', 'Usuario desconocido')


    def _init_chat(self, payload, IDRedSocial):
        """
        Lógica para crear/actualizar chat y guardar mensaje entrante.
        """
        entry = payload.get('entry', [])[0]
        msg   = entry.get('messaging', [])[0]

        sender_admin = msg['recipient']['id']
        sender_id    = msg['sender']['id']
        text         = msg.get('message', {}).get('text', '')

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
            chat.save()
            user_name = chat.Nombre
        else:
            # Obtener nombre de usuario desde la API
            user_name = self._get_user_name(sender_id, setting.Token)
            chat = Messenger.objects.create(
                IDRedSocial=IDRedSocial,
                IDSender=sender_id,
                Nombre=user_name,
                Estado=1
            )

        # Fechas en español
        now = timezone.localtime()
        Fecha = now.strftime('%d %B %Y')  # ej. '09 mayo 2025'
        Hora  = now.strftime('%H:%M')

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
        chat.Nombre     = user_name if user_name != 'Usuario desconocido' else f'{user_name} {chat.IDChat}'
        chat.updated_at = now
        chat.save()

        # Marcar como vistos todos los anteriores con Estado=1
        MessengerMensaje.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)
