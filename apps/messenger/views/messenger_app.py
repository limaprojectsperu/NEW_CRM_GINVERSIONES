import os
import json
import requests
from django.utils import timezone
from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion

class MessengerSendView(APIView):
    """
    POST /api/messenger-app/send-message/
    """

    # Valores por defecto (serán sobrescritos en _init_setting)
    token = 'EAAN6ZAaynJIsBOzTMpM26MQHPu2xrWYF94e3l4Sd0DYWsCRZC1TwtRpDe30Xt7ayZBLQk7oxn82PPBl3z4JON3LUmZAQwq34k8j4VXvldB89agq1aIdN8ZBGJggMkdyh1vJhUoZAIVTPaYijDjmJPjyVFmzt0nOhWiROgChsEIkaB3CqEDqbuuNhCUZCwBcxtS7'
    token_hook = 'hookTokenMessage2024'
    url_api = 'https://graph.facebook.com/v20.0/133662089823062'

    def post(self, request):
        # Carga configuración dinámica de token/url
        self._init_setting(request.data.get('IDRedSocial'))

        # Validación de tokenHook
        if request.data.get('tokenHook') != self.token_hook:
            return Response({
                'message': 'El Token Hook es inválido.',
                'data': None,
                'status': 400,
            }, status=status.HTTP_400_BAD_REQUEST)

        recipient = request.data.get('IdRecipient')
        text_msg  = request.data.get('Mensaje', '')
        result_api = None

        # 1) Procesar media si existe
        media = self._send_media(request)
        if media:
            payload = self._build_payload(recipient,
                                          request.data.get('type'),
                                          text_msg,
                                          media)
            result_api = self._send_msg_api(payload)

        # 2) Enviar texto siempre que haya mensaje
        if text_msg:
            payload = self._build_payload(recipient, 'text', text_msg)
            result_api = self._send_msg_api(payload)

        # 3) Guardar en base de datos
        mensaje_obj = self._save_message(request, media.get('path') if media else None)

        return Response({
            'message': 'Mensaje enviado con éxito.',
            'lastMessage': {
                'IDChatMensaje': mensaje_obj.IDChatMensaje,
                'IDChat': mensaje_obj.IDChat,
                'Mensaje': mensaje_obj.Mensaje,
                'Fecha': mensaje_obj.Fecha,
                'Hora': mensaje_obj.Hora,
                'Url': mensaje_obj.Url,
                'Extencion': mensaje_obj.Extencion,
                'Estado': mensaje_obj.Estado,
            },
            'resultMedia': media,
            'data': result_api.get('response') if result_api else None,
            'status': result_api.get('status_code') if result_api else None,
        })


    def _send_msg_api(self, payload_json):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json',
        }
        resp = requests.post(f'{self.url_api}/messages',
                             headers=headers,
                             data=payload_json)
        return {
            'response': resp.json(),
            'status_code': resp.status_code
        }


    def _send_media(self, request):
        """
        Subida de media a Facebook y guardado local.
        """
        upload = request.FILES.get('file')
        if not upload:
            return None

        # Request multipart a FB
        multipart = {
            'message': (None, json.dumps({
                'attachment': {
                    'type': request.data.get('type'),
                    'payload': {'is_reusable': True}
                }
            }), 'application/json'),
            'filedata': (upload.name, upload.read(), upload.content_type),
            'type': (None, request.data.get('typeMedia')),
        }
        headers = {'Authorization': f'Bearer {self.token}'}

        resp = requests.post(f'{self.url_api}/message_attachments',
                             files=multipart,
                             headers=headers)
        data = resp.json()

        # Crear la carpeta si no existe
        sender_id = request.data.get("IDSender")
        media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
        folder_path = os.path.join(media_dir, 'messenger', sender_id)
        os.makedirs(folder_path, exist_ok=True)
        
        # Guardar archivo en disco usando solo el timestamp
        extension = os.path.splitext(upload.name)[1]
        filename = f'{int(timezone.now().timestamp())}{extension}'
        rel_path = f'media/messenger/{sender_id}/{filename}'
        
        # Reiniciar el puntero del archivo ya que se leyó en el multipart
        upload.seek(0)
        default_storage.save(rel_path, upload)

        return {
            'status_code': resp.status_code,
            'response': data,
            'path': f"{settings.MEDIA_URL.rstrip('/')}/messenger/{sender_id}/{filename}"
        }


    def _build_payload(self, recipient_id, msg_type, text='', media=None):
        """
        Construye el JSON a enviar.
        """
        if msg_type == 'text':
            body = {
                "recipient": {"id": recipient_id},
                "messaging_type": "RESPONSE",
                "message": {"text": text}
            }
        else:
            body = {
                "recipient": {"id": recipient_id},
                "message": {
                    "attachment": {
                        "type": msg_type,
                        "payload": {
                            "attachment_id": media.get('response', {}).get('attachment_id')
                        }
                    }
                }
            }
        return json.dumps(body)


    def _save_message(self, request, url=None):
        """
        Guarda el mensaje en MessengerMensaje y actualiza updated_at del chat.
        """
        msg = MessengerMensaje.objects.create(
            IDChat    = request.data.get('IDChat'),
            IDSender  = request.data.get('IDSender'),
            Mensaje   = request.data.get('Mensaje'),
            Fecha     = request.data.get('Fecha'),
            Hora      = request.data.get('Hora'),
            Url       = url,
            Extencion = request.data.get('Extencion'),
            Estado    = 1
        )
        Messenger.objects.filter(IDChat=request.data.get('IDChat')).update(
            updated_at=timezone.now()
        )
        return msg


    def _init_setting(self, IDRedSocial):
        """
        Carga token, tokenHook y urlApi desde MessengerConfiguracion.
        """
        cfg = MessengerConfiguracion.objects.filter(IDRedSocial=IDRedSocial).first()
        if cfg:
            self.token      = cfg.Token
            self.token_hook = cfg.TokenHook
            self.url_api    = cfg.urlApi
