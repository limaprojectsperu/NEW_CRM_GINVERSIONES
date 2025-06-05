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
        # Para URL local, usar la URL recibida; para archivo subido, usar la generada
        file_url = None
        if media:
            file_url = media.get('path') if 'path' in media else request.data.get('urlFile')
        
        mensaje_obj = self._save_message(request, file_url)

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
                'origen': mensaje_obj.origen,
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
        Envía archivo a Facebook desde URL local del servidor Django.
        """
        try:
            # Construir ruta completa del archivo
            # Basándose en MEDIA_ROOT = BASE_DIR y MEDIA_URL = '/media/'
            if os.path.isabs(url_file):
                # Si es ruta absoluta, usarla directamente
                file_path = url_file
            else:
                # url_file viene como "/media/messenger/plantillas/file.jpg"
                # Como MEDIA_ROOT = BASE_DIR, necesitamos quitar solo la primera barra
                clean_path = url_file.lstrip('/')
                file_path = os.path.join(settings.MEDIA_ROOT, clean_path)
            
            # Normalizar la ruta
            file_path = os.path.normpath(file_path)
            
            if not os.path.exists(file_path):
                return {
                    'status_code': 404,
                    'response': {
                        'error': f'Archivo no encontrado: {file_path}',
                        'url_received': url_file,
                        'media_root': str(settings.MEDIA_ROOT),
                        'base_dir': str(settings.BASE_DIR)
                    },
                    'path': url_file
                }

            # Leer archivo desde disco
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
            # Obtener información del archivo
            filename = os.path.basename(file_path)
            file_extension = os.path.splitext(filename)[1].lower()
            
            # Determinar content_type basado en la extensión
            content_type_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.mp4': 'video/mp4', '.avi': 'video/avi',
                '.mp3': 'audio/mpeg', '.wav': 'audio/wav',
                '.pdf': 'application/pdf',
                '.doc': 'application/msword',
                '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
            }
            content_type = content_type_map.get(file_extension, 'application/octet-stream')

            # Request multipart a Facebook
            multipart = {
                'message': (None, json.dumps({
                    'attachment': {
                        'type': request.data.get('type'),
                        'payload': {'is_reusable': True}
                    }
                }), 'application/json'),
                'filedata': (filename, file_data, content_type),
                'type': (None, request.data.get('typeMedia')),
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            resp = requests.post(f'{self.url_api}/message_attachments',
                                 files=multipart,
                                 headers=headers)
            data = resp.json()

            return {
                'status_code': resp.status_code,
                'response': data,
                'path': url_file  # Retornar la URL original
            }
            
        except Exception as e:
            return {
                'status_code': 500,
                'response': {'error': f'Error procesando archivo: {str(e)}'},
                'path': url_file
            }


    def _send_media_from_upload(self, request, upload):
        """
        Comportamiento original: subir archivo desde FormData.
        """
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
            Estado    = 1,
            origen = request.data.get('origen', 1)
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