import os
import json
import requests
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status

from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes
from apps.utils.datetime_func import get_naive_peru_time, get_naive_peru_time_delta

class WhatsappSendAPIView(APIView):
    """
    POST /api/whatsapp-app/send-message/
    """

    # Valores por defecto; se sobrescriben en _init_setting()
    token      = 'EAAhTfopaHd4BOwe…'
    token_hook = 'hookTokenLaravel2023'
    url_api    = 'https://graph.facebook.com/v18.0/211229238731236'
    template   = 'hello_world'
    language   = 'en_US'

    def post(self, request):
        data = request.data

        # 1) Cargar configuración dinámica
        self._init_setting(data.get('IDRedSocial'))

        # 2) Validar tokenHook
        if data.get('tokenHook') != self.token_hook:
            return JsonResponse({
                'message': 'El Token Hook es inválido.',
                'data': None,
                'status': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        phone   = data.get('phone')
        text    = data.get('Mensaje', '')
        result  = None

        # 3) Buscar chat reciente para plantilla
        chat = Whatsapp.objects.filter(
            IDRedSocial=data.get('IDRedSocial'),
            Telefono=phone,
            FechaUltimaPlantilla__gt=get_naive_peru_time_delta(days=-1)
        ).first()

        # 4) Si no hay chat reciente o mensaje == “plantilla”, enviamos template
        if not chat or text.lower() == 'plantilla':
            payload = self._build_template_payload(phone)
            result  = self._send_msg_api(payload)
            if result['status_code'] == 200:
                Whatsapp.objects.filter(IDChat=data.get('IDChat')).update(
                    FechaUltimaPlantilla=get_naive_peru_time()
                )
        else:
            # 5) Procesar media (subida o URL)
            media = self._send_media(request)
            if media:
                payload = self._build_media_payload(phone, data.get('type'), media, data.get('name'))
                result  = self._send_msg_api(payload)
            # 6) Enviar texto adicional
            if text:
                payload = self._build_text_payload(phone, text)
                result  = self._send_msg_api(payload)

        # 7) Guardar mensaje en BD
        saved = self._save_message(request, media.get('path') if locals().get('media') else None)

        return JsonResponse({
            'message': 'ok',
            'lastMessage': {
                'IDChatMensaje': saved.IDChatMensaje,
                'IDChat':       saved.IDChat,
                'Mensaje':      saved.Mensaje,
                'Fecha':        saved.Fecha,
                'Hora':         saved.Hora,
                'Url':          saved.Url,
                'Extencion':    saved.Extencion,
                'Estado':       saved.Estado,
            },
            'resultMedia': media if locals().get('media') else None,
            'data':        result.get('response')   if result else None,
            'status':      result.get('status_code') if result else None,
        }, status=result.get('status_code', 200))

    def _init_setting(self, IDRedSocial):
        cfg = WhatsappConfiguracion.objects.filter(IDRedSocial=IDRedSocial).first()
        if not cfg:
            return
        self.token      = cfg.Token
        self.token_hook = cfg.TokenHook
        self.url_api    = cfg.urlApi
        self.template   = cfg.Template
        self.language   = cfg.Language

    def _send_msg_api(self, payload_json):
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type':  'application/json',
        }
        resp = requests.post(f'{self.url_api}/messages',
                             headers=headers,
                             data=payload_json)
        return {
            'response':    resp.json(),
            'status_code': resp.status_code
        }

    def _send_media(self, request):
        """
        Soporta subida de archivo (request.FILES['file']) o URL local (request.data['urlFile'])
        """
        # 1) URL local
        url_file = request.data.get('urlFile')
        if url_file:
            return self._send_media_from_url(request, url_file)
        # 2) Upload multipart
        upload = request.FILES.get('file')
        if upload:
            return self._send_media_from_upload(request, upload)
        return None

    def _send_media_from_url(self, request, url_file):
        """
        Envía archivo a WhatsApp API desde URL local del servidor Django.
        Similar al comportamiento de Messenger pero adaptado para WhatsApp.
        """
        try:
            # Construir ruta completa del archivo
            # Basándose en MEDIA_ROOT = BASE_DIR y MEDIA_URL = '/media/'
            if os.path.isabs(url_file):
                # Si es ruta absoluta, usarla directamente
                file_path = url_file
            else:
                # url_file viene como "/media/whatsapp/plantillas/file.jpg"
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

            # Request multipart a WhatsApp API (diferente estructura que Messenger)
            multipart = {
                'file': (filename, file_data, content_type),
                'messaging_product': (None, 'whatsapp'),
                'type': (None, request.data.get('typeMedia')),
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            # WhatsApp usa el endpoint /media (no /message_attachments como Messenger)
            resp = requests.post(f'{self.url_api}/media',
                                files=multipart,
                                headers=headers)

            return {
                'status_code': resp.status_code,
                'response': resp.json(),
                'path': url_file  # Retornar la URL original sin guardar
            }
            
        except Exception as e:
            return {
                'status_code': 500,
                'response': {'error': f'Error procesando archivo: {str(e)}'},
                'path': url_file
            }

    def _send_media_from_upload(self, request, upload):
        # multipart a Facebook API + guardado en disk
        filename    = f'{int(timezone.now().timestamp())}{os.path.splitext(upload.name)[1]}'
        rel_path    = f'whatsapp/{request.data.get("IDChat")}/{filename}'
        default_storage.save(rel_path, upload)
        multipart   = {
            'file':        (upload.name, upload.read(), upload.content_type),
            'messaging_product': (None, 'whatsapp'),
            'type':        (None, request.data.get('typeMedia')),
        }
        headers     = {'Authorization': f'Bearer {self.token}'}
        resp        = requests.post(f'{self.url_api}/media',
                                    files=multipart,
                                    headers=headers)
        return {
            'status_code': resp.status_code,
            'response':    resp.json(),
            'path':        default_storage.url(rel_path)
        }

    def _build_template_payload(self, to_phone):
        return json.dumps({
            "messaging_product": "whatsapp",
            "to":                to_phone,
            "type":              "template",
            "template": {
                "name":     self.template,
                "language": {"code": self.language}
            }
        })

    def _build_text_payload(self, to_phone, body):
        return json.dumps({
            "messaging_product": "whatsapp",
            "to":                to_phone,
            "type":              "text",
            "text": {"body": body, "preview_url": False}
        })

    def _build_media_payload(self, to_phone, media_type, media, filename):
        return json.dumps({
            "messaging_product": "whatsapp",
            "to":                to_phone,
            "type":              media_type,
            media_type: {"id": media['response'].get('id')}
        })

    def _save_message(self, request, url=None):
        msg = WhatsappMensajes.objects.create(
            IDChat    = request.data.get('IDChat'),
            Telefono  = request.data.get('phone'),
            Mensaje   = request.data.get('Mensaje'),
            Fecha     = request.data.get('Fecha'),
            Hora      = request.data.get('Hora'),
            Url       = url,
            Extencion = request.data.get('Extencion'),
            Estado    = 1
        )
        Whatsapp.objects.filter(IDChat=request.data.get('IDChat')).update(
            updated_at=get_naive_peru_time()
        )
        return msg
