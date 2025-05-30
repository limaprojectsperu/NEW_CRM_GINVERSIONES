import requests
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes
from ...utils.pusher_client import pusher_client

# Si dispone de utilidades para fechas en Perú:
from apps.utils.datetime_func import get_date_tiem, get_naive_peru_time

class WhatsappWebhookAPIView(APIView):
    """
    GET  /api/web-hooks/app/<int:IDRedSocial>/    -> verifica token y responde hub_challenge
    POST /api/web-hooks/app/<int:IDRedSocial>/    -> recibe mensajes de WhatsApp y guarda en BD
    """

    def get(self, request, IDRedSocial):
        hub_challenge   = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        hub_mode        = request.GET.get('hub.mode', '')

        setting = WhatsappConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()

        if hub_mode == 'subscribe' and setting and setting.TokenHook == hub_verify_token:
            return HttpResponse(hub_challenge)
        return HttpResponseForbidden()

    def post(self, request, IDRedSocial):
        payload = request.data
        if not payload:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        self._init_chat(payload, IDRedSocial)
        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 'IDRedSocial': IDRedSocial })
        return Response({'status': 'ok'})

    def _init_chat(self, payload, IDRedSocial):
        entry   = payload.get('entry', [])[0]
        change  = entry.get('changes', [])[0]['value']
        # Datos según la carga de WhatsApp
        phone_admin = change['metadata']['display_phone_number']
        phone       = change['messages'][0]['from']
        message     = change['messages'][0]['text']['body']
        name        = change['contacts'][0]['profile']['name']

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
            chat.save()
        else:
            chat = Whatsapp.objects.create(
                IDRedSocial          = setting.IDRedSocial,
                Nombre               = name,
                Telefono             = phone,
                Estado               = 1
            )

        # Fechas en formato local Perú
        try:
            Fecha, Hora = get_date_tiem()
        except ImportError:
            now = timezone.now()
            Fecha = now.strftime('%d %B %Y')
            Hora  = now.strftime('%H:%M')

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
        chat.FechaUltimaPlantilla = timezone.now()
        chat.updated_at           = timezone.now()  # o get_naive_peru_time()
        chat.save()

        # Marcar como vistos los mensajes anteriores
        WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)