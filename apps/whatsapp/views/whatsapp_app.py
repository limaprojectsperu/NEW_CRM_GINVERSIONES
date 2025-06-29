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
from apps.users.views.wasabi import get_wasabi_file_data, save_file_to_wasabi

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
        media   = None

        # 3) Buscar chat reciente para plantilla
        chat = Whatsapp.objects.filter(
            IDRedSocial=data.get('IDRedSocial'),
            Telefono=phone,
            FechaUltimaPlantilla__gt=get_naive_peru_time_delta(days=-1)
        ).first()

        # 4) Si no hay chat reciente o mensaje == "plantilla", enviamos template
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
            
            # 6) Enviar texto adicional (solo si hay texto)
            if text:
                payload = self._build_text_payload(phone, text)
                result  = self._send_msg_api(payload)

        # 7) Guardar mensaje en BD
        file_url = None
        if media:
            file_url = media.get('path')
        
        saved = self._save_message(request, file_url)

        return JsonResponse({
            'message': 'Mensaje enviado con éxito.',
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
            'resultMedia': media,
            'data':        result.get('response')   if result else None,
            'status':      result.get('status_code') if result else None,
        }, status=result.get('status_code', 200) if result else 200)

    def _init_setting(self, IDRedSocial):
        """Carga configuración dinámica desde la BD"""
        cfg = WhatsappConfiguracion.objects.filter(IDRedSocial=IDRedSocial).first()
        if cfg:
            self.token      = cfg.Token
            self.token_hook = cfg.TokenHook
            self.url_api    = cfg.urlApi
            self.template   = cfg.Template
            self.language   = cfg.Language

    def _send_msg_api(self, payload_json):
        """Envía mensaje a la API de WhatsApp"""
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type':  'application/json',
        }
        try:
            resp = requests.post(f'{self.url_api}/messages',
                               headers=headers,
                               data=payload_json,
                               timeout=30)
            return {
                'response':    resp.json() if resp.text else {},
                'status_code': resp.status_code
            }
        except requests.exceptions.RequestException as e:
            return {
                'response':    {'error': f'Error de conexión: {str(e)}'},
                'status_code': 500
            }

    def _send_media(self, request):
        """
        Soporta subida de archivo (request.FILES['file']) o URL local (request.data['urlFile'])
        """
        # 1) URL local (nueva funcionalidad)
        url_file = request.data.get('urlFile')
        if url_file:
            return self._send_media_from_url(request, url_file)
        
        # 2) Upload multipart (funcionalidad original)
        upload = request.FILES.get('file')
        if upload:
            return self._send_media_from_upload(request, upload)
        
        return None

    def _send_media_from_url(self, request, url_file):
        """
        Envía archivo a WhatsApp API desde URL usando get_wasabi_file_data unificado.
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

            # Request multipart a WhatsApp API
            files = {
                'file': (file_result['filename'], file_result['file_data'], file_result['content_type']),
            }
            data_form = {
                'messaging_product': 'whatsapp',
                'type': request.data.get('typeMedia', 'document'),
            }
            headers = {'Authorization': f'Bearer {self.token}'}

            resp = requests.post(f'{self.url_api}/media',
                               files=files,
                               data=data_form,
                               headers=headers,
                               timeout=60)

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
        Maneja archivos subidos via FormData - ACTUALIZADO para guardar en Wasabi
        """
        try:
            # Obtener teléfono para crear la estructura de carpetas
            telefono = request.data.get("Telefono", "unknown")
            
            # Generar nombre único para el archivo
            timestamp = int(timezone.now().timestamp())
            extension = os.path.splitext(upload.name)[1] if upload.name else ''
            filename = f'{timestamp}{extension}'
            rel_path = f'media/whatsapp/{telefono}/{filename}'
            
            # Leer el archivo una sola vez
            upload.seek(0)
            file_data = upload.read()
            
            # Enviar a WhatsApp API
            files = {
                'file': (upload.name, file_data, upload.content_type),
            }
            data_form = {
                'messaging_product': 'whatsapp',
                'type': request.data.get('typeMedia', 'document'),
            }
            headers = {'Authorization': f'Bearer {self.token}'}
            
            resp = requests.post(f'{self.url_api}/media',
                            files=files,
                            data=data_form,
                            headers=headers,
                            timeout=60)
            
            # Guardar archivo en Wasabi
            wasabi_result = save_file_to_wasabi(file_data, rel_path, upload.content_type)
            
            # Construir URL de respuesta
            file_url = f"{settings.MEDIA_URL.rstrip('/')}/whatsapp/{telefono}/{filename}"
            
            response_data = {
                'status_code': resp.status_code,
                'response': resp.json() if resp.text else {},
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
                'response': {'error': f'Error subiendo archivo: {str(e)}'},
                'path': None,
                'storage': 'error'
            }

    def _build_template_payload(self, to_phone):
        """Construye payload para plantilla"""
        return json.dumps({
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": self.template,
                "language": {"code": self.language}
            }
        })

    def _build_text_payload(self, to_phone, body):
        """Construye payload para mensaje de texto"""
        return json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body
            }
        })

    def _build_media_payload(self, to_phone, media_type, media, filename=None):
        """Construye payload para envío de media - CORREGIDO"""
        media_content = {"id": media['response'].get('id')}
        
        # Para documentos, agregar filename si se proporciona
        if media_type == 'document' and filename:
            media_content["filename"] = filename
            
        return json.dumps({
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to_phone,
            "type": media_type,
            media_type: media_content
        })

    def _save_message(self, request, url=None):
        """Guarda mensaje en la BD"""
        msg = WhatsappMensajes.objects.create(
            IDChat    = request.data.get('IDChat'),
            Telefono  = request.data.get('Telefono'),
            Mensaje   = request.data.get('Mensaje'),
            Fecha     = request.data.get('Fecha'),
            Hora      = request.data.get('Hora'),
            Url       = url,
            Extencion = request.data.get('Extencion'),
            Estado    = 1
        )
        
        # Actualizar timestamp del chat
        Whatsapp.objects.filter(IDChat=request.data.get('IDChat')).update(
            updated_at=get_naive_peru_time()
        )
        
        return msg