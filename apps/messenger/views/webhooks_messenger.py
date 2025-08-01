import requests
import json
import os
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, HttpResponseForbidden
from django.conf import settings
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion
from apps.redes_sociales.models import MessengerPlantilla
from ...utils.pusher_client import pusher_client
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.datetime_func import get_naive_peru_time, get_date_time
from apps.utils.tokens_phone import get_user_tokens_by_access_id
from apps.openai.openai_chatbot import ChatbotService
from django.test import RequestFactory
from rest_framework.request import Request
from ..views.messenger_app import MessengerSendView
from rest_framework.parsers import JSONParser
from apps.utils.find_states import find_state_id
from apps.users.views.wasabi import save_file_to_wasabi

chatbot = ChatbotService()

class WebhookVerifyReceive(APIView):
    """
    GET /api/webhooks-messenger/app/{IDRedSocial}/
    Verifica el token de Facebook y devuelve hub_challenge.
    """
    def get(self, request, IDRedSocial):
        hub_mode = request.GET.get('hub.mode', '')
        hub_challenge = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        
        setting = MessengerConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()
        
        if hub_mode and hub_verify_token:
            if hub_mode == 'subscribe' and setting and setting.TokenHook == hub_verify_token:
                return HttpResponse(hub_challenge)
            else:
                return HttpResponseForbidden()
        
        return HttpResponseForbidden()

    """
    POST /api/webhooks-messenger/app/{IDRedSocial}/
    Recibe la carga útil JSON de Facebook en webhook.
    """
    def post(self, request, IDRedSocial):
        payload = request.data
        if not payload:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            self._init_chat(payload, IDRedSocial)
        except (KeyError, IndexError) as e:
            print(f"Error al procesar el payload de Messenger: {e}")
            return Response({'status': 'error processing payload but acknowledged'})

        return Response({'status': 'ok'})

    def _get_user_name(self, sender_id, setting):
        """
        Obtiene el nombre del usuario desde la API de Facebook
        """
        url = f"{setting.url_graph_v}/{sender_id}"
        try:
            resp = requests.get(url, params={
                'fields': 'name',
                'access_token': setting.Token
            }, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get('name', 'Usuario desconocido')
            else:
                return 'Usuario desconocido'
        except (requests.RequestException, ValueError):
            return 'Usuario desconocido'

    def _init_chat(self, payload, IDRedSocial):
        """
        Lógica para crear/actualizar chat y guardar mensaje entrante.
        """
        entry = payload.get('entry', [])[0]
        msg = entry.get('messaging', [])[0]

        sender_admin = msg['recipient']['id']
        sender_id = msg['sender']['id']
        
        # Obtener el mensaje y determinar el tipo
        message_obj = msg.get('message', {})
        message_content = ""
        message_notification = ""
        media_info = None
        
        # Cargamos configuración
        setting = MessengerConfiguracion.objects.filter(
            IDRedSocial=IDRedSocial
        ).first()
        
        if not setting:
            return

        # Procesar diferentes tipos de mensajes
        if 'text' in message_obj:
            message_content = message_obj['text']
        
        elif 'attachments' in message_obj:
            attachments = message_obj['attachments']
            if attachments:
                attachment = attachments[0]
                attachment_type = attachment.get('type')
                
                if attachment_type == 'image':
                    media_info = self._process_media_attachment(attachment, 'image', setting, sender_id)
                    message_notification = 'Imagen'
                
                elif attachment_type == 'video':
                    media_info = self._process_media_attachment(attachment, 'video', setting, sender_id)
                    message_notification = 'Video'
                
                elif attachment_type == 'audio':
                    media_info = self._process_media_attachment(attachment, 'audio', setting, sender_id)
                    message_notification = 'Audio'
                
                elif attachment_type == 'file':
                    media_info = self._process_media_attachment(attachment, 'file', setting, sender_id)
                    message_notification = 'Archivo'
                
                elif attachment_type == 'template':
                    # Manejo de plantillas (botones, carruseles, etc.)
                    template = attachment.get('payload', {})
                    if template.get('template_type') == 'button':
                        message_content = template.get('text', '[Plantilla con botones]')
                    else:
                        message_content = '[Plantilla]'
                
                else:
                    message_content = f'[{attachment_type.capitalize()}]'
        
        elif 'quick_reply' in message_obj:
            # Respuesta rápida
            quick_reply = message_obj['quick_reply']
            message_content = message_obj.get('text', '[Respuesta rápida]')
        
        elif 'postback' in msg:
            # Postback de botones
            postback = msg['postback']
            message_content = postback.get('title', '[Postback]')
        
        else:
            # Otros tipos de mensajes
            message_content = '[Mensaje no soportado]'
            print(f"Tipo de mensaje no soportado")
            return

        #if not message_content or not message_notification:
            #print("No se pudo extraer el contenido del mensaje")
            #return

        newChat = False

        # Buscamos chat existente
        chat = Messenger.objects.filter(
            IDRedSocial=IDRedSocial,
            IDSender=sender_id
        ).first()

        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes + 1
            chat.save()
            user_name = chat.Nombre
        else:
            # Obtener nombre de usuario desde la API
            user_name = self._get_user_name(sender_id, setting)
            chat = Messenger.objects.create(
                IDRedSocial=IDRedSocial,
                IDSender=sender_id,
                Nombre=user_name,
                nuevos_mensajes=1,
                Estado=1
            )
            newChat = True

        # Guardar el mensaje
        mensaje_obj = self._save_incoming_message(chat, sender_id, message_content, media_info)
        
        # Respuesta automática
        if newChat:
            template = MessengerPlantilla.objects.filter(
                marca_id=setting.marca_id, 
                estado=True, 
                tipo=1
            ).first()
            if template:
                self.send_message(setting, chat, template.mensaje)

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
        
        # Open AI
        if setting.openai and chat.openai:
            self.open_ai_response(setting, chat)

        # Push notification
        firebase_service = FirebaseServiceV1()
        tokens = get_user_tokens_by_access_id('04010000')
        if len(tokens) > 0:
            firebase_service.send_to_multiple_devices(
                tokens=tokens,
                title="Nuevo mensaje en Messenger",
                body=message_content if message_content else message_notification,
                data={'type': 'router', 'route_name': 'MessengerPage'}
            )

        pusher_client.trigger('py-messenger-channel', 'PyMessengerEvent', { 
            'IDRedSocial': IDRedSocial,
            'IDChat': mensaje_obj.IDChat,
            'mensaje': lastMessage 
            })


    def _process_media_attachment(self, attachment, media_type, setting, sender_id):
        """
        Procesa adjuntos multimedia de Messenger
        """
        try:
            payload = attachment.get('payload', {})
            media_url = payload.get('url')
            
            if not media_url:
                print(f"No se encontró URL para {media_type}")
                return None

            media_info = {
                'type': media_type,
                'url': media_url,
                'is_reusable': payload.get('is_reusable', False)
            }

            # Información específica por tipo
            if media_type == 'image':
                media_info['sticker_id'] = payload.get('sticker_id')
            elif media_type == 'video':
                media_info['is_reusable'] = payload.get('is_reusable', False)
            elif media_type == 'file':
                media_info['filename'] = payload.get('filename', 'archivo_sin_nombre')

            # Descargar y guardar archivo
            file_info = self._download_and_save_media(media_url, media_info, setting, sender_id)
            if file_info:
                media_info.update(file_info)

            return media_info

        except Exception as e:
            print(f"Error procesando media {media_type}: {e}")
            return None

    def _download_and_save_media(self, media_url, media_info, setting, sender_id):
        """
        Descarga archivo de Messenger y lo guarda en Wasabi
        """
        try:
            # Descargar archivo
            response = requests.get(media_url, timeout=60)
            if response.status_code != 200:
                print(f"Error descargando archivo: {response.status_code}")
                return None

            # Determinar extensión y nombre de archivo
            content_type = response.headers.get('content-type', '')
            extension = self._get_file_extension_from_content_type(content_type, media_info)
            
            timestamp = int(timezone.now().timestamp())
            filename = f"{timestamp}{extension}"
            
            # Ruta final en Wasabi
            final_path = f"media/messenger/{sender_id}/{filename}"

            # Guardar en Wasabi
            wasabi_result = save_file_to_wasabi(
                response.content,
                final_path,
                content_type or 'application/octet-stream'
            )

            if wasabi_result['success']:
                file_size = len(response.content)
                final_url = f"{settings.MEDIA_URL.rstrip('/')}/messenger/{sender_id}/{filename}"
                
                return {
                    'local_path': final_url,
                    'filename': filename,
                    'size': file_size,
                    'storage': 'wasabi',
                    'content_type': content_type
                }
            else:
                print(f"Error guardando en Wasabi: {wasabi_result['error']}")
                return None

        except Exception as e:
            print(f"Error descargando/guardando archivo: {e}")
            return None

    def _get_file_extension_from_content_type(self, content_type, media_info):
        """
        Obtiene extensión del archivo basada en content-type
        """
        # Si es archivo y tiene nombre, usar su extensión
        if media_info.get('type') == 'file' and media_info.get('filename'):
            return os.path.splitext(media_info['filename'])[1]
        
        # Mapeo de content-type a extensión
        content_type_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'video/mp4': '.mp4',
            'video/quicktime': '.mov',
            'video/x-msvideo': '.avi',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.mp4',
            'audio/ogg': '.ogg',
            'audio/wav': '.wav',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
            'text/plain': '.txt',
            'application/zip': '.zip',
            'application/x-rar-compressed': '.rar',
        }
        
        return content_type_to_ext.get(content_type, '')

    def _save_incoming_message(self, chat, sender_id, message_content, media_info=None):
        """
        Guarda mensaje entrante en la base de datos
        """
        Fecha, Hora = get_date_time()
        
        url = None
        extension_data = None
        
        if media_info:
            url = media_info.get('local_path')
            
            extension_data = {
                'name': media_info.get('filename', 'archivo'),
                'size': media_info.get('size', 0),
                'type': media_info.get('content_type', 'application/octet-stream'),
                'extension': media_info.get('filename', '').split('.')[-1] if media_info.get('filename') else '',
                'media_type': media_info.get('type'),
                'is_reusable': media_info.get('is_reusable', False)
            }
            
            # Información específica por tipo
            if media_info.get('type') == 'image':
                extension_data['sticker_id'] = media_info.get('sticker_id')

        # Guardar mensaje
        new_msg = MessengerMensaje.objects.create(
            IDChat=chat.IDChat,
            IDSender=sender_id,
            Mensaje=message_content,
            Fecha=Fecha,
            Hora=Hora,
            Url=url,
            Extencion=json.dumps(extension_data) if extension_data else None,
            Estado=2,
            origen=2
        )

        # Actualizar chat
        user_name = chat.Nombre or 'Usuario desconocido'
        if user_name == 'Usuario desconocido':
            nombreChat = f'Usuario desconocido {chat.IDChat}'
        else:
            nombreChat = user_name

        chat.Nombre = nombreChat
        chat.updated_at = get_naive_peru_time()
        chat.save()

        # Marcar como vistos todos los anteriores con Estado=1
        MessengerMensaje.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)

        return new_msg

    def open_ai_response(self, setting, chat):
        """
        Genera respuesta usando OpenAI
        """
        ultimos_mensajes = list(MessengerMensaje.objects.filter(
            IDChat=chat.IDChat
        ).order_by('-IDChatMensaje')[:10])
        ultimos_mensajes.reverse()
        
        messages = []
        
        for entry in ultimos_mensajes:
            role = "assistant" if entry.IDSender == setting.IDSender else "user"
            messages.append({"role": role, "content": entry.Mensaje})
        
        res = chatbot.get_response(setting.marca_id, messages)
        self.send_message(setting, chat, res, 3)

        chat.respuesta_generada_openai = True
        chat.save()

    def send_message(self, setting, chat, mensaje, origen=1):
        """
        Envía mensaje usando MessengerSendView
        """
        Fecha, Hora = get_date_time()

        message_data = {
            "IDRedSocial": setting.IDRedSocial,
            "tokenHook": setting.TokenHook,  
            "IdRecipient": chat.IDSender,
            "IDChat": chat.IDChat,
            "IDSender": setting.IDSender,
            "Mensaje": mensaje,
            "Fecha": Fecha,
            "Hora": Hora,
            "origen": origen,
        }
        
        factory = RequestFactory()
        django_request = factory.post(
            '/api/messenger-app/send-message/',
            data=json.dumps(message_data),
            content_type='application/json'
        )
        
        drf_request = Request(django_request, parsers=[JSONParser()])
        view = MessengerSendView()
        response = view.post(drf_request)
        
        return response