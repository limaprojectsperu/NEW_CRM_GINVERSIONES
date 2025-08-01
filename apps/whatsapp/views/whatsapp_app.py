import os
import json
import requests
from django.conf import settings
from django.utils import timezone
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework import status
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes, WhatsappMetaPlantillas
from apps.utils.datetime_func import get_naive_peru_time, get_naive_peru_time_delta
from apps.users.views.wasabi import get_wasabi_file_data, save_file_to_wasabi
from ...utils.pusher_client import pusher_client

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
        setting = self._init_setting(data.get('IDRedSocial'))

        # 2) Validar tokenHook
        if data.get('tokenHook') != self.token_hook:
            return JsonResponse({
                'message': 'El Token Hook es inválido.',
                'data': None,
                'status': 400
            }, status=status.HTTP_400_BAD_REQUEST)

        phone   = data.get('phone')
        text    = data.get('Mensaje', '')
        message_24_hours = data.get('message_24_hours', True)
        result  = None
        media   = None
        msjPlantilla = None
        
        # 3) Buscar chat reciente para plantilla
        chat = Whatsapp.objects.filter(
            IDRedSocial=data.get('IDRedSocial'),
            Telefono=phone,
            FechaUltimaPlantilla__gt=get_naive_peru_time_delta(days=-1)
        ).first()

        # 4) Si no hay chat reciente o mensaje == "plantilla", enviamos template
        if not chat or text.lower() == 'plantilla':
            # NUEVA FUNCIONALIDAD: Soporte para plantillas con variables e imágenes
            media_id = data.get('media_id')
            template_params = None
            template_name = None
            
            if data.get('template_params'):
                template_params = data.get('template_params')
            else:
                template_params = [data.get('template_params_1', 'Emprendedor'), data.get('template_params_2', setting.Nombre)]
                
            if data.get('template_name'):
                template_name = data.get('template_name')
            
            # Obtener plantilla desde BD
            template_obj = WhatsappMetaPlantillas.objects.filter(
                nombre=template_name if template_name else self.template
            ).first()

            media_type = template_obj.tipo
            
            # Si no se proporciona media_id pero la plantilla tiene media_url, subir automáticamente
            if not media_id and template_obj and template_obj.media_url and template_obj.media_url.strip():
                media_result = self._upload_template_media(template_obj)
                if media_result['success']:
                    media_id = media_result['media_id']
                    media_type = media_result['media_type']
                else:
                    return JsonResponse({
                        'message': f'Error al subir media de la plantilla: {media_result["error"]}',
                        'status': 500
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            payload = self._build_template_payload(phone, template_params, media_id, media_type, template_obj.nombre)
            result  = self._send_msg_api(payload)
            
            if result['status_code'] == 200:
                Whatsapp.objects.filter(IDChat=data.get('IDChat')).update(
                    FechaUltimaPlantilla=get_naive_peru_time()
                )
                message_text = self._build_message_text(template_obj, template_params, bool(media_id))
                if message_24_hours:
                    msjPlantilla = f"Ya pasaron más de 24 horas desde el ultimo mensaje, por ello se envió una plantilla: {message_text}"
                else:
                    msjPlantilla = f"{message_text}"
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
        
        saved = self._save_message(request, file_url, msjPlantilla)

        lastMessage = {
            'IDChatMensaje': saved.IDChatMensaje,
            'IDChat':       saved.IDChat,
            'Telefono':     saved.Telefono,
            'Mensaje':      saved.Mensaje,
            'Fecha':        saved.Fecha,
            'Hora':         saved.Hora,
            'Url':          saved.Url,
            'Extencion':    saved.Extencion,
            'Estado':       saved.Estado,
            'user_id':      saved.user_id
        }

        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 
            'IDRedSocial': setting.IDRedSocial, 
            'IDChat': saved.IDChat,
            'mensaje': lastMessage
            })

        return JsonResponse({
            'message': 'Mensaje enviado con éxito.',
            'lastMessage': lastMessage,
            'resultMedia': media,
            'data':        result.get('response')   if result else None,
            'status':      result.get('status_code') if result else None,
            'template_media_uploaded': bool(media_id if not chat else False),
            'media_id': media_id if not chat else None,
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

        return cfg

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

    def _upload_template_media(self, template):
        """Sube automáticamente el media de la plantilla desde la carpeta media"""
        try:
            # Construir ruta del archivo
            media_path = os.path.join(settings.MEDIA_ROOT, 'media', template.media_url.lstrip('/media/'))
            
            # Verificar si el archivo existe
            if not os.path.exists(media_path):
                return {
                    'success': False,
                    'error': f'Archivo no encontrado: {media_path}'
                }
            
            # Determinar tipo de media basado en la extensión o tipo de plantilla
            media_type = self._determine_media_type(media_path, template.tipo)
            
            # Leer archivo
            with open(media_path, 'rb') as file:
                file_content = file.read()
                file_name = os.path.basename(media_path)
                
                # Determinar content_type
                content_type = self._get_content_type(file_name)
                
                # Preparar datos para upload
                files = {
                    'file': (file_name, file_content, content_type)
                }
                
                data = {
                    'messaging_product': 'whatsapp',
                    'type': media_type
                }
                
                headers = {
                    'Authorization': f'Bearer {self.token}'
                }
                
                # Subir a WhatsApp API
                response = requests.post(
                    f'{self.url_api}/media',
                    files=files,
                    data=data,
                    headers=headers,
                    timeout=60
                )
                
                if response.status_code == 200:
                    response_data = response.json()
                    return {
                        'success': True,
                        'media_id': response_data.get('id'),
                        'media_type': media_type,
                        'file_path': media_path
                    }
                else:
                    return {
                        'success': False,
                        'error': f'Error en API de WhatsApp: {response.text}'
                    }
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Error procesando archivo: {str(e)}'
            }

    def _determine_media_type(self, file_path, template_type):
        """Determina el tipo de media basado en la extensión del archivo y tipo de plantilla"""
        # Si el tipo de plantilla está definido y es válido, usarlo
        valid_types = ['image', 'video', 'audio', 'document']
        if template_type and template_type.lower() in valid_types:
            return template_type.lower()
        
        # Determinar por extensión
        extension = os.path.splitext(file_path)[1].lower()
        
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        video_extensions = ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm']
        audio_extensions = ['.mp3', '.wav', '.aac', '.ogg', '.m4a']
        
        if extension in image_extensions:
            return 'image'
        elif extension in video_extensions:
            return 'video'
        elif extension in audio_extensions:
            return 'audio'
        else:
            return 'document'

    def _get_content_type(self, file_name):
        """Obtiene el content-type basado en la extensión del archivo"""
        extension = os.path.splitext(file_name)[1].lower()
        
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.mp4': 'video/mp4',
            '.avi': 'video/x-msvideo',
            '.mov': 'video/quicktime',
            '.wmv': 'video/x-ms-wmv',
            '.flv': 'video/x-flv',
            '.webm': 'video/webm',
            '.mp3': 'audio/mpeg',
            '.wav': 'audio/wav',
            '.aac': 'audio/aac',
            '.ogg': 'audio/ogg',
            '.m4a': 'audio/mp4',
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.xls': 'application/vnd.ms-excel',
            '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        }
        
        return content_types.get(extension, 'application/octet-stream')

    def _build_template_payload(self, to_phone, template_params=None, media_id=None, media_type='image', template_name=None):
        """Construye payload para plantilla con soporte para variables e imágenes"""
        template_name_to_use = template_name if template_name else self.template
        
        template = WhatsappMetaPlantillas.objects.filter(
            nombre=template_name_to_use
        ).first()

        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "template",
            "template": {
                "name": template.nombre,
                "language": {"code": template.lenguaje}
            }
        }

        # Agregar componentes si hay parámetros o media
        components = []
        
        # Componente de header con media
        if media_id:
            # Determinar el tipo de media y construir el parámetro apropiado
            media_param = {
                "type": media_type
            }
            
            # Agregar el media según su tipo
            if media_type == "image":
                media_param["image"] = {"id": media_id}
            elif media_type == "document":
                media_param["document"] = {"id": media_id}
            elif media_type == "video":
                media_param["video"] = {"id": media_id}
            elif media_type == "audio":
                media_param["audio"] = {"id": media_id}
            else:
                # Default a imagen si no se especifica
                media_param["image"] = {"id": media_id}
            
            components.append({
                "type": "header",
                "parameters": [media_param]
            })
        
        # Componente de body con parámetros
        if template_params:
            body_params = []
            for param in template_params:
                body_params.append({
                    "type": "text",
                    "text": str(param)
                })
            
            components.append({
                "type": "body",
                "parameters": body_params
            })
        
        # Agregar componentes al payload si existen
        if components:
            payload["template"]["components"] = components

        return json.dumps(payload)

    def _build_message_text(self, template, params=None, has_media=False):
        """Construye el texto del mensaje para guardar en BD"""
        if not template:
            return "Plantilla enviada"
            
        message_text = template.mensaje

        if not message_text:
            # Si no hay mensaje en la plantilla, usar la descripción como fallback.
            message_text = f"Plantilla: {template.descripcion}"
        elif params:
            # Reemplazar cada placeholder {{n}} con el parámetro correspondiente.
            for i, param in enumerate(params):
                # El placeholder es {{1}}, {{2}}, etc. El índice de la lista es 0, 1, ...
                placeholder = f"{{{{{i + 1}}}}}"
                message_text = message_text.replace(placeholder, str(param))

        return message_text

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

    def _save_message(self, request, url=None, msjPlantilla=None):
        """Guarda mensaje en la BD"""
        msg = WhatsappMensajes.objects.create(
            IDChat    = request.data.get('IDChat'),
            Telefono  = request.data.get('Telefono'),
            Mensaje   = msjPlantilla if msjPlantilla else request.data.get('Mensaje'),
            Fecha     = request.data.get('Fecha'),
            Hora      = request.data.get('Hora'),
            Url       = url,
            Extencion = request.data.get('Extencion'),
            Estado    = 1,
            origen    = request.data.get('origen', 1),
            user_id   = request.headers.get('userid', None)
        )
        
        # Actualizar timestamp del chat
        Whatsapp.objects.filter(IDChat=request.data.get('IDChat')).update(
            updated_at=get_naive_peru_time()
        )
        
        return msg