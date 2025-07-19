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
from apps.utils.datetime_func  import get_naive_peru_time
from apps.users.views.wasabi import get_wasabi_file_data, save_file_to_wasabi
from ...utils.pusher_client import pusher_client

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
        setting = self._init_setting(request.data.get('IDRedSocial'))

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
        # Para URL local, usar la URL recibida; para archivo subido, usar la generada
        file_url = None
        if media:
            file_url = media.get('path') if 'path' in media else request.data.get('urlFile')
        
        mensaje_obj = self._save_message(request, file_url)

        lastMessage = {
            'IDChatMensaje': mensaje_obj.IDChatMensaje,
            'IDChat': mensaje_obj.IDChat,
            'IDSender': mensaje_obj.IDSender,
            'Mensaje': mensaje_obj.Mensaje,
            'Fecha': mensaje_obj.Fecha,
            'Hora': mensaje_obj.Hora,
            'Url': mensaje_obj.Url,
            'Extencion': mensaje_obj.Extencion,
            'Estado': mensaje_obj.Estado,
            'origen': mensaje_obj.origen,
            'user_id': mensaje_obj.user_id
        }

        pusher_client.trigger('py-messenger-channel', 'PyMessengerEvent', { 
            'IDRedSocial': setting.IDRedSocial,
            'IDChat': mensaje_obj.IDChat,
            'mensaje': lastMessage 
            })

        return Response({
            'message': 'Mensaje enviado con éxito.',
            'lastMessage': lastMessage,
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
        Maneja media de dos formas:
        1. Archivo subido (file) - comportamiento original
        2. URL de archivo local (urlFile) - nuevo comportamiento
        """
        # Verificar si es URL de archivo local
        url_file = request.data.get('urlFile')
        if url_file:
            return self._send_media_from_url(request, url_file)
        
        # Comportamiento original: archivo subido
        upload = request.FILES.get('file')
        if not upload:
            return None

        return self._send_media_from_upload(request, upload)


    def _send_media_from_url(self, request, url_file):
        """
        Envía archivo a Facebook desde URL usando get_wasabi_file_data unificado.
        """
        try:
            # Usar la función unificada para obtener el archivo
            file_result = get_wasabi_file_data(url_file)
            
            if not file_result['success']:
                return {
                    'status_code': 404,
                    'response': {
                        'error': file_result['error'],
                        'url_received': url_file,
                        'source_checked': file_result['source']
                    },
                    'path': url_file
                }

            # Request multipart a Facebook
            multipart = {
                'message': (None, json.dumps({
                    'attachment': {
                        'type': request.data.get('type'),
                        'payload': {'is_reusable': True}
                    }
                }), 'application/json'),
                'filedata': (file_result['filename'], file_result['file_data'], file_result['content_type']),
                'type': (None, request.data.get('typeMedia')),
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            resp = requests.post(f'{self.url_api}/message_attachments',
                                 files=multipart,
                                 headers=headers)
            
            return {
                'status_code': resp.status_code,
                'response': resp.json() if resp.text else {},
                'path': url_file,
                'source': file_result['source']  # Incluir fuente del archivo
            }
            
        except Exception as e:
            return {
                'status_code': 500,
                'response': {'error': f'Error procesando archivo: {str(e)}'},
                'path': url_file
            }

    def _send_media_from_upload(self, request, upload):
        """
        Comportamiento original: subir archivo desde FormData - ACTUALIZADO para guardar en Wasabi.
        """
        try:
            # Leer el archivo una sola vez
            upload.seek(0)
            file_data = upload.read()
            
            # Request multipart a FB
            multipart = {
                'message': (None, json.dumps({
                    'attachment': {
                        'type': request.data.get('type'),
                        'payload': {'is_reusable': True}
                    }
                }), 'application/json'),
                'filedata': (upload.name, file_data, upload.content_type),
                'type': (None, request.data.get('typeMedia')),
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            resp = requests.post(f'{self.url_api}/message_attachments',
                                 files=multipart,
                                 headers=headers)
            data = resp.json()

            # Crear nombre de archivo y ruta para Wasabi
            sender_id = request.data.get("IDSender", "unknown")
            timestamp = int(timezone.now().timestamp())
            extension = os.path.splitext(upload.name)[1] if upload.name else ''
            filename = f'{timestamp}{extension}'
            rel_path = f'media/messenger/{sender_id}/{filename}'
            
            # Guardar archivo en Wasabi
            wasabi_result = save_file_to_wasabi(file_data, rel_path, upload.content_type)
            
            # Construir URL de respuesta
            file_url = f"{settings.MEDIA_URL.rstrip('/')}/messenger/{sender_id}/{filename}"
            
            response_data = {
                'status_code': resp.status_code,
                'response': data,
                'path': file_url,
                'storage': 'wasabi' if wasabi_result['success'] else 'failed'
            }
            
            # Agregar información de error si falló el guardado en Wasabi
            if not wasabi_result['success']:
                response_data['storage_error'] = wasabi_result['error']
            
            return response_data
            
        except Exception as e:
            return {
                'status_code': 500,
                'response': {'error': f'Error procesando archivo: {str(e)}'},
                'path': None,
                'storage': 'error'
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
            Estado    = 1,
            origen = request.data.get('origen', 1),
            user_id = request.headers.get('userid', None)
        )

        Messenger.objects.filter(IDChat=request.data.get('IDChat')).update(
            updated_at=get_naive_peru_time()
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

        return cfg