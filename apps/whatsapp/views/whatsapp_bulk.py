import json
import os
import requests
from django.http import JsonResponse
from django.conf import settings
from rest_framework.views import APIView
from rest_framework import status
from django.utils import timezone
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes, WhatsappMetaPlantillas
from apps.utils.datetime_func import get_date_time, get_naive_peru_time
from apps.utils.find_states import find_state_id


class WhatsappBulkSendAPIView(APIView):
    """
    POST /api/whatsapp-app/send-bulk-message/
    
    Envía mensajes en bloque usando plantillas de WhatsApp
    """
    
    def post(self, request):
        data = request.data
        
        # Validar campos requeridos
        required_fields = ['IDRedSocial', 'tokenHook', 'template_name', 'phone_numbers']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'message': f'El campo {field} es requerido.',
                    'status': 400
                }, status=status.HTTP_400_BAD_REQUEST)
        
        # Cargar configuración
        setting = self._get_configuration(data.get('IDRedSocial'))
        if not setting:
            return JsonResponse({
                'message': 'Configuración de WhatsApp no encontrada.',
                'status': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Validar tokenHook
        if data.get('tokenHook') != setting.TokenHook:
            return JsonResponse({
                'message': 'El Token Hook es inválido.',
                'status': 400
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Buscar plantilla
        template = self._get_template(data.get('template_name'))
        if not template:
            return JsonResponse({
                'message': 'Plantilla no encontrada.',
                'status': 404
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Procesar media automáticamente si la plantilla tiene media_url
        media_id = data.get('media_id')
        media_type = data.get('media_type', 'image')
        
        # Si no se proporciona media_id pero la plantilla tiene media_url, subir automáticamente
        if not media_id and template.media_url and template.media_url.strip():
            media_result = self._upload_template_media(setting, template)
            if media_result['success']:
                media_id = media_result['media_id']
                media_type = media_result['media_type']
            else:
                return JsonResponse({
                    'message': f'Error al subir media de la plantilla: {media_result["error"]}',
                    'status': 500
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Procesar envío en bloque
        phone_numbers = data.get('phone_numbers', [])
        template_params = data.get('template_params', [])
        save_message = data.get('save_message', True)
        
        results = self._send_bulk_messages(
            setting=setting,
            template=template,
            phone_numbers=phone_numbers,
            template_params=template_params,
            save_message=save_message,
            media_id=media_id,
            media_type=media_type
        )
        
        return JsonResponse({
            'message': 'Mensajes enviados con éxito.',
            'results': results,
            'template_media_uploaded': bool(media_id and template.media_url),
            'media_id': media_id,
            'summary': {
                'total': len(phone_numbers),
                'success': len([r for r in results if r['success']]),
                'failed': len([r for r in results if not r['success']])
            },
            'status': 200
        }, status=status.HTTP_200_OK)
    
    def _get_configuration(self, IDRedSocial):
        """Obtiene la configuración de WhatsApp"""
        return WhatsappConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial,
            Estado=1
        ).first()
    
    def _get_template(self, template_name):
        """Obtiene la plantilla por nombre"""
        return WhatsappMetaPlantillas.objects.filter(
            nombre=template_name,
            estado=1
        ).first()
    
    def _upload_template_media(self, setting, template):
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
                    'Authorization': f'Bearer {setting.Token}'
                }
                
                # Subir a WhatsApp API
                response = requests.post(
                    f'{setting.urlApi}/media',
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
    
    def _send_bulk_messages(self, setting, template, phone_numbers, template_params, save_message, media_id=None, media_type='image'):
        """Envía mensajes en bloque"""
        results = []
        
        for i, phone in enumerate(phone_numbers):
            try:
                # Obtener parámetros específicos para este teléfono
                params = template_params[i] if i < len(template_params) else []
                
                # Construir payload de la plantilla
                payload = self._build_template_payload(
                    phone=phone,
                    template=template,
                    params=params,
                    media_id=media_id,
                    media_type=media_type
                )
                
                # Enviar mensaje
                result = self._send_template_message(setting, payload)
                
                # Procesar resultado
                if result['status_code'] == 200:
                    # Guardar mensaje si se requiere
                    if save_message:
                        self._process_chat_and_message(
                            setting=setting,
                            phone=phone,
                            template=template,
                            params=params,
                            has_media=bool(media_id)
                        )
                    
                    results.append({
                        'phone': phone,
                        'success': True,
                        'message': 'Mensaje enviado exitosamente',
                        'whatsapp_id': result['response'].get('messages', [{}])[0].get('id'),
                        'status_code': result['status_code']
                    })
                else:
                    results.append({
                        'phone': phone,
                        'success': False,
                        'message': 'Error al enviar mensaje',
                        'error': result['response'].get('error', {}),
                        'status_code': result['status_code']
                    })
                    
            except Exception as e:
                results.append({
                    'phone': phone,
                    'success': False,
                    'message': f'Error procesando teléfono: {str(e)}',
                    'status_code': 500
                })
        
        return results
    
    def _build_template_payload(self, phone, template, params, media_id=None, media_type='image'):
        """Construye el payload para la plantilla"""
        payload = {
            "messaging_product": "whatsapp",
            "to": phone,
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
        if params:
            body_params = []
            for param in params:
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
    
    def _send_template_message(self, setting, payload):
        """Envía el mensaje de plantilla a WhatsApp API"""
        headers = {
            'Authorization': f'Bearer {setting.Token}',
            'Content-Type': 'application/json',
        }
        
        try:
            response = requests.post(
                f'{setting.urlApi}/messages',
                headers=headers,
                data=payload,
                timeout=30
            )
            
            return {
                'response': response.json() if response.text else {},
                'status_code': response.status_code
            }
            
        except requests.exceptions.RequestException as e:
            return {
                'response': {'error': f'Error de conexión: {str(e)}'},
                'status_code': 500
            }
    
    def _process_chat_and_message(self, setting, phone, template, params, has_media=False):
        """Procesa el chat y guarda el mensaje"""
        current_time = get_naive_peru_time()
        contact_name = phone 
        if params and len(params) > 0:
            contact_name = str(params[0])
        
        # Buscar o crear chat
        chat = Whatsapp.objects.filter(
            IDRedSocial=setting.IDRedSocial,
            Telefono=phone
        ).first()
        
        if chat:
            # Actualizar chat existente
            chat.FechaUltimaPlantilla = current_time
            chat.updated_at = current_time
            chat.Estado = 1
            chat.save()
        else:
            # Crear nuevo chat
            chat = Whatsapp.objects.create(
                IDRedSocial=setting.IDRedSocial,
                Nombre=contact_name, 
                Telefono=phone,
                FechaUltimaPlantilla=current_time,
                updated_at=current_time,
                IDEL=find_state_id(2, 'No leído'),
                Estado=1
            )
        
        # Construir mensaje para guardar
        message_text = self._build_message_text(template, params, has_media)
        Fecha, Hora = get_date_time()
        
        # Guardar mensaje enviado
        WhatsappMensajes.objects.create(
            IDChat=chat.IDChat,
            Telefono=setting.Telefono,
            Mensaje=message_text,
            Fecha=Fecha,
            Hora=Hora,
            Estado=1,  # Enviado
            origen=1   # Default
        )
        
        return chat
    
    def _build_message_text(self, template, params, has_media=False):
        """Construye el texto del mensaje para guardar en BD"""
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

        # Opcionalmente, agregar una nota si el mensaje incluye un archivo.
        if has_media:
            message_text += " (Con archivo adjunto)"

        return message_text