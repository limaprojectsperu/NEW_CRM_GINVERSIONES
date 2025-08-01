import requests
import json
import os
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes, WhatsapChatUser, WhatsapChatUserHistorial, Lead
from apps.redes_sociales.models import MessengerPlantilla
from ...utils.pusher_client import pusher_client
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.datetime_func import get_date_time, get_naive_peru_time
from apps.utils.tokens_phone import get_user_tokens_by_whatsapp
from apps.openai.openai_chatbot import ChatbotService
from django.test import RequestFactory
from rest_framework.request import Request
from ..views.whatsapp_app import WhatsappSendAPIView
from rest_framework.parsers import JSONParser
from apps.utils.find_states import find_state_id, find_substate_id
from apps.users.views.wasabi import save_file_to_wasabi
from apps.users.models import Users

chatbot = ChatbotService()

class WhatsappWebhookAPIView(APIView):
    """
    GET   /api/web-hooks/app     -> verifica token y responde hub_challenge
    POST  /api/web-hooks/app     -> recibe mensajes de WhatsApp y guarda en BD
    """

    def get(self, request):
        hub_challenge   = request.GET.get('hub.challenge', '')
        hub_verify_token = request.GET.get('hub.verify_token', '')
        hub_mode        = request.GET.get('hub.mode', '')

        setting = WhatsappConfiguracion.objects.filter(Estado=1).first()

        if hub_mode == 'subscribe' and setting and setting.TokenHook == hub_verify_token:
            return HttpResponse(hub_challenge)
        return HttpResponseForbidden()

    def post(self, request):
        payload = request.data
        if not payload:
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            self._init_chat(payload)
        except (KeyError, IndexError) as e:
            print(f"Error al procesar el payload de WhatsApp: {e}")
            return Response({'status': 'error processing payload but acknowledged'})

        return Response({'status': 'ok'})

    def _init_chat(self, payload):
        entry   = payload.get('entry', [])[0]
        change  = entry.get('changes', [])[0]['value']

        if 'messages' not in change:
            return

        message_obj = change['messages'][0]
        message_type = message_obj.get('type')

        phone_admin = change['metadata']['display_phone_number']
        setting = WhatsappConfiguracion.objects.filter(Telefono=phone_admin).first()
        if not setting:
            return

        phone = message_obj['from']

        message_content = ""
        message_notification = ""
        button_id = None
        media_info = None
        
        # Manejo de diferentes tipos de mensajes
        if message_type == 'button':
            button_data = message_obj.get('button', {})
            message_content = button_data.get('text', '')
            button_id = button_data.get('payload', '')
        
        elif message_type == 'interactive':
            interactive = message_obj.get('interactive', {})
            if 'button_reply' in interactive:
                button_reply = interactive['button_reply']
                message_content = button_reply.get('title', '')
                button_id = button_reply.get('id', '')
            elif 'list_reply' in interactive:
                list_reply = interactive['list_reply']
                message_content = list_reply.get('title', '')
                button_id = list_reply.get('id', '')
            else:
                return

        elif message_type == 'text':
            message_content = message_obj['text']['body']
        
        elif message_type == 'image':
            media_info = self._process_media_message(message_obj, 'image', setting, phone)
            message_notification = 'Imagen'
        
        elif message_type == 'audio':
            media_info = self._process_media_message(message_obj, 'audio', setting, phone)
            message_notification = 'Audio'
        
        elif message_type == 'video':
            media_info = self._process_media_message(message_obj, 'video', setting, phone)
            message_notification = 'Video'
        
        elif message_type == 'document':
            media_info = self._process_media_message(message_obj, 'document', setting, phone)
            message_notification = 'Documento'
        
        elif message_type == 'voice':
            media_info = self._process_media_message(message_obj, 'voice', setting, phone)
            message_notification = 'Nota de voz'
        
        elif message_type == 'sticker':
            media_info = self._process_media_message(message_obj, 'sticker', setting, phone)
            message_notification = 'Sticker'
        
        else:
            print(f"Tipo de mensaje no soportado: {message_type}")
            return

        #if not message_content or not message_notification:
            #print("No se pudo extraer el contenido del mensaje")
            #return
            
        contacts = change.get('contacts', [])
        name = phone
        if contacts and len(contacts) > 0:
            profile = contacts[0].get('profile', {})
            name = profile.get('name', phone)

        chat = self._get_or_create_chat(setting, phone, name)
        saved = self._save_incoming_message(chat, phone, message_content, media_info, button_id)
        self._handle_auto_response(setting, chat, message_content)

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

        # Push notification
        firebase_service = FirebaseServiceV1()
        tokens = get_user_tokens_by_whatsapp(setting.IDRedSocial, chat.IDChat)
        if len(tokens) > 0:
            firebase_service.send_to_multiple_devices(
                tokens=tokens,
                title="Nuevo mensaje en WhatsApp",
                body=message_content if message_content else message_notification,
                data={'type': 'router', 'route_name': 'WhatsappPage'}
            )

        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 
            'IDRedSocial': setting.IDRedSocial,
            'IDChat': chat.IDChat, 
            'mensaje': lastMessage
            })


    def _process_media_message(self, message_obj, media_type, setting, phone):
        """
        Procesa mensajes multimedia y descarga/almacena archivos
        """
        try:
            media_data = message_obj.get(media_type, {})
            media_id = media_data.get('id')
            
            if not media_id:
                print(f"No se encontró ID de media para {media_type}")
                return None

            media_info = {
                'id': media_id,
                'type': media_type,
                'mime_type': media_data.get('mime_type'),
                'sha256': media_data.get('sha256'),
                'filename': media_data.get('filename'),
                'caption': media_data.get('caption'),
                'voice': media_data.get('voice', False)
            }

            if media_type == 'audio':
                media_info['duration'] = media_data.get('duration')
                media_info['voice'] = media_data.get('voice', False)
            elif media_type == 'video':
                media_info['duration'] = media_data.get('duration')
            elif media_type == 'image':
                media_info['caption'] = media_data.get('caption')
            elif media_type == 'document':
                media_info['filename'] = media_data.get('filename')

            file_info = self._download_and_save_media(media_id, media_info, setting, phone)
            if file_info:
                media_info.update(file_info)

            return media_info

        except Exception as e:
            print(f"Error procesando media {media_type}: {e}")
            return None

    def _download_and_save_media(self, media_id, media_info, setting, phone):
        """
        Descarga archivo de WhatsApp API y lo guarda en Wasabi directamente en la ruta final.
        """
        try:
            headers = { 'Authorization': f'Bearer {setting.Token}' }
            url_info = f"{setting.url_graph_v}/{media_id}"
            
            response = requests.get(url_info, headers=headers, timeout=30)
            if response.status_code != 200:
                print(f"Error obteniendo info del archivo: {response.status_code}")
                return None

            file_info = response.json()
            file_url = file_info.get('url')
            if not file_url:
                return None

            file_response = requests.get(file_url, headers=headers, timeout=60)
            if file_response.status_code != 200:
                print(f"Error descargando archivo: {file_response.status_code}")
                return None

            timestamp = int(timezone.now().timestamp())
            extension = self._get_file_extension(media_info)
            filename = f"{timestamp}{extension}"
            
            final_path = f"media/whatsapp/{phone}/{filename}"

            wasabi_result = save_file_to_wasabi(
                file_response.content,
                final_path, # Usar la ruta final
                media_info.get('mime_type', 'application/octet-stream')
            )

            if wasabi_result['success']:
                file_size = len(file_response.content)
                final_url = f"{settings.MEDIA_URL.rstrip('/')}/whatsapp/{phone}/{filename}"
                
                return {
                    'local_path': final_url, # URL final
                    'filename': filename,
                    'size': file_size,
                    'storage': 'wasabi'
                }
            else:
                print(f"Error guardando en Wasabi: {wasabi_result['error']}")
                return None

        except Exception as e:
            print(f"Error descargando/guardando archivo: {e}")
            return None

    def _get_file_extension(self, media_info):
        """
        Obtiene extensión del archivo basada en mime_type o filename
        """
        if media_info.get('filename'):
            return os.path.splitext(media_info['filename'])[1]
        
        mime_to_ext = {
            'image/jpeg': '.jpg', 'image/png': '.png', 'image/gif': '.gif',
            'image/webp': '.webp', 'audio/mpeg': '.mp3', 'audio/mp4': '.mp4',
            'audio/ogg': '.ogg', 'video/mp4': '.mp4', 'video/quicktime': '.mov',
            'application/pdf': '.pdf', 'application/msword': '.doc',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
            'application/vnd.ms-excel': '.xls',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': '.xlsx',
        }
        
        mime_type = media_info.get('mime_type', '')
        return mime_to_ext.get(mime_type, '')

    def _get_or_create_chat(self, setting, phone, name):
        """
        Obtiene o crea un chat
        """
        chat = Whatsapp.objects.filter(
            IDRedSocial=setting.IDRedSocial,
            Telefono=phone
        ).first()
        
        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes + 1
            chat.save()
        else:
            chat.nuevos_mensajes = chat.nuevos_mensajes + 1
            chat = Whatsapp.objects.create(
                IDRedSocial=setting.IDRedSocial,
                Telefono=phone,
                Nombre=name,
                nuevos_mensajes=1,
                IDEL=find_state_id(2, setting.IDRedSocial, 'PENDIENTE DE LLAMADA'),
                IDSubEstadoLead=find_substate_id(2, setting.IDRedSocial, 'LEAD ASIGNADO, NO CONTACTADO'),
                Estado=1
            )

        return chat

    def _save_incoming_message(self, chat, phone, message_content, media_info=None, button_id=None):
        """
        Guarda mensaje entrante en la base de datos
        """
        Fecha, Hora = get_date_time()
        
        url = None
        extension_data = None
        
        if media_info:
            # La URL ya es la ruta final, no se necesita manipulación
            url = media_info.get('local_path')
            
            extension_data = {
                'name': media_info.get('filename', 'archivo'),
                'size': media_info.get('size', 0),
                'type': media_info.get('mime_type', 'application/octet-stream'),
                'extension': media_info.get('filename', '').split('.')[-1] if media_info.get('filename') else '',
                'media_type': media_info.get('type'),
                'duration': media_info.get('duration')
            }
            
            if media_info.get('type') == 'audio':
                extension_data['audio'] = True
                extension_data['voice'] = media_info.get('voice', False)

        mensaje_guardado = WhatsappMensajes.objects.create(
            IDChat=chat.IDChat,
            Telefono=phone,
            Mensaje=message_content,
            Fecha=Fecha,
            Hora=Hora,
            Url=url,
            Extencion=json.dumps(extension_data) if extension_data else None,
            Estado=2,
            origen=2
        )

        dateNative = get_naive_peru_time()
        chat.FechaUltimaPlantilla = dateNative
        chat.updated_at = dateNative 
        chat.save()

        WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)

        return mensaje_guardado

    def _handle_auto_response(self, setting, chat, message_content):
        """
        Maneja respuestas automáticas y OpenAI
        """
        if chat.nuevos_mensajes == 1:
            template = MessengerPlantilla.objects.filter(
                marca_id=setting.marca_id, 
                estado=True, 
                tipo=1
            ).first()
            if template:
                self.send_message(setting, chat, template.mensaje)

        respom_setting_ia = True
        chat_user = WhatsapChatUser.objects.filter(IDChat=chat.IDChat).first()
        if(chat_user):
            user = Users.objects.filter(co_usuario=chat_user.user_id).first()
            if user and user.openai:
                respom_setting_ia = False
                self.open_ai_response(setting, chat)

        if respom_setting_ia and setting.openai and chat.openai:
            self.open_ai_response(setting, chat)

    def open_ai_response(self, setting, chat):
        """
        Genera respuesta usando OpenAI
        """
        ultimos_mensajes = list(WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat
        ).order_by('-IDChatMensaje')[:10])
        ultimos_mensajes.reverse()
        
        messages = [{"role": "assistant" if entry.Telefono == setting.Telefono else "user", "content": entry.Mensaje} for entry in ultimos_mensajes]
        print(messages)
        res = chatbot.get_response(setting.marca_id, messages)
        self.send_message(setting, chat, res, 3)

        chat.respuesta_generada_openai = True
        chat.save()   

    def send_message(self, setting, chat, mensaje, origen=1):
        """
        Envía mensaje usando WhatsappSendAPIView
        """
        Fecha, Hora = get_date_time()
        message_data = {
            "IDRedSocial": setting.IDRedSocial,
            "tokenHook": setting.TokenHook,  
            "phone": chat.Telefono,
            "IDChat": chat.IDChat,
            "Telefono": setting.Telefono,
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
        view = WhatsappSendAPIView()
        return view.post(drf_request)