import requests
import json
import os
from django.http import HttpResponse, HttpResponseForbidden
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.conf import settings
from ..models import WhatsappConfiguracion, Whatsapp, WhatsappMensajes
from apps.redes_sociales.models import MessengerPlantilla
from ...utils.pusher_client import pusher_client
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.datetime_func import get_date_time, get_naive_peru_time
from apps.utils.tokens_phone import get_user_tokens_by_permissions
from apps.openai.openai_chatbot import ChatbotService
from django.test import RequestFactory
from rest_framework.request import Request
from ..views.whatsapp_app import WhatsappSendAPIView
from rest_framework.parsers import JSONParser
from apps.utils.find_states import find_state_id
from apps.users.views.wasabi import save_file_to_wasabi

chatbot = ChatbotService()

class WhatsappWebhookAPIView(APIView):
    """
    GET  /api/web-hooks/app    -> verifica token y responde hub_challenge
    POST /api/web-hooks/app   -> recibe mensajes de WhatsApp y guarda en BD
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

        # Verificar si hay mensajes o si es una actualización de estado
        if 'messages' not in change:
            print("No hay mensajes en el payload")
            return 

        message_obj = change['messages'][0]
        message_type = message_obj.get('type')
        
        print(f"Tipo de mensaje: {message_type}")
        print(f"Mensaje completo: {json.dumps(message_obj, indent=2)}")

        # Obtener configuración primero
        phone_admin = change['metadata']['display_phone_number']
        setting = WhatsappConfiguracion.objects.filter(Telefono=phone_admin).first()
        if not setting:
            print(f"No se encontró configuración para el teléfono: {phone_admin}")
            return 

        message_content = ""
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
        
        # NUEVOS TIPOS DE MENSAJES MULTIMEDIA
        elif message_type == 'image':
            media_info = self._process_media_message(message_obj, 'image', setting)
            message_content = media_info.get('caption', '[Imagen]') if media_info else '[Imagen]'
        
        elif message_type == 'audio':
            media_info = self._process_media_message(message_obj, 'audio', setting)
            message_content = '[Audio]'
        
        elif message_type == 'video':
            media_info = self._process_media_message(message_obj, 'video', setting)
            message_content = media_info.get('caption', '[Video]') if media_info else '[Video]'
        
        elif message_type == 'document':
            media_info = self._process_media_message(message_obj, 'document', setting)
            if media_info:
                filename = media_info.get('filename', 'documento')
                message_content = f'[Documento: {filename}]'
            else:
                message_content = '[Documento]'
        
        elif message_type == 'voice':
            media_info = self._process_media_message(message_obj, 'voice', setting)
            message_content = '[Nota de voz]'
        
        elif message_type == 'sticker':
            media_info = self._process_media_message(message_obj, 'sticker', setting)
            message_content = '[Sticker]'
        
        else:
            print(f"Tipo de mensaje no soportado: {message_type}")
            return

        # Validar que tenemos contenido del mensaje
        if not message_content:
            print("No se pudo extraer el contenido del mensaje")
            return

        # Obtener datos del mensaje
        phone = message_obj['from']
        
        # Obtener nombre del contacto
        contacts = change.get('contacts', [])
        name = phone
        if contacts and len(contacts) > 0:
            profile = contacts[0].get('profile', {})
            name = profile.get('name', phone)

        # Crear o actualizar el chat
        chat = self._get_or_create_chat(setting, phone, name)

        # Guardar mensaje
        self._save_incoming_message(chat, phone, message_content, media_info, button_id)

        # Respuesta automática y notificaciones
        self._handle_auto_response(setting, chat, message_content)

        pusher_client.trigger('py-whatsapp-channel', 'PyWhatsappEvent', { 'IDRedSocial': setting.IDRedSocial })

    def _process_media_message(self, message_obj, media_type, setting):
        """
        Procesa mensajes multimedia y descarga/almacena archivos
        """
        try:
            media_data = message_obj.get(media_type, {})
            media_id = media_data.get('id')
            
            if not media_id:
                print(f"No se encontró ID de media para {media_type}")
                return None

            # Información básica del archivo
            media_info = {
                'id': media_id,
                'type': media_type,
                'mime_type': media_data.get('mime_type'),
                'sha256': media_data.get('sha256'),
                'filename': media_data.get('filename'),  # Solo para documentos
                'caption': media_data.get('caption'),    # Para imágenes/videos
                'voice': media_data.get('voice', False)  # Para audio
            }

            # Información específica por tipo
            if media_type == 'audio':
                media_info['duration'] = media_data.get('duration')
                media_info['voice'] = media_data.get('voice', False)
            elif media_type == 'video':
                media_info['duration'] = media_data.get('duration')
            elif media_type == 'image':
                media_info['caption'] = media_data.get('caption')
            elif media_type == 'document':
                media_info['filename'] = media_data.get('filename')

            # Descargar y guardar archivo
            file_info = self._download_and_save_media(media_id, media_info, setting)
            if file_info:
                media_info.update(file_info)

            return media_info

        except Exception as e:
            print(f"Error procesando media {media_type}: {e}")
            return None

    def _download_and_save_media(self, media_id, media_info, setting):
        """
        Descarga archivo de WhatsApp API y lo guarda en Wasabi
        """
        try:
            # 1. Obtener URL del archivo desde WhatsApp API
            headers = {
                'Authorization': f'Bearer {setting.Token}',
            }
            
            # Construir URL correcta para obtener info del media
            url_info = f"{setting.url_graph_v}/{media_id}"
            print(f"Obteniendo info del archivo desde: {url_info}")
            
            response = requests.get(url_info, headers=headers, timeout=30)
            
            if response.status_code != 200:
                print(f"Error obteniendo info del archivo: {response.status_code}")
                print(f"Respuesta: {response.text}")
                return None

            file_info = response.json()
            file_url = file_info.get('url')
            
            if not file_url:
                print("No se obtuvo URL del archivo")
                return None

            # 2. Descargar archivo
            file_response = requests.get(file_url, headers=headers, timeout=60)
            
            if file_response.status_code != 200:
                print(f"Error descargando archivo: {file_response.status_code}")
                print(f"Respuesta: {file_response.text}")
                return None

            # 3. Generar nombre y ruta del archivo
            timestamp = int(timezone.now().timestamp())
            extension = self._get_file_extension(media_info)
            filename = f"{timestamp}{extension}"
            
            # Crear nombre temporal primero
            temp_path = f"media/whatsapp/temp/{filename}"

            # 4. Guardar en Wasabi
            wasabi_result = save_file_to_wasabi(
                file_response.content,
                temp_path,
                media_info.get('mime_type', 'application/octet-stream')
            )

            if wasabi_result['success']:
                # Construir información del archivo guardado
                file_size = len(file_response.content)
                file_url = f"{settings.MEDIA_URL.rstrip('/')}/whatsapp/temp/{filename}"
                
                return {
                    'local_path': file_url,
                    'filename': filename,
                    'size': file_size,
                    'storage': 'wasabi',
                    'temp_path': temp_path
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
        # Si hay filename, usar su extensión
        if media_info.get('filename'):
            return os.path.splitext(media_info['filename'])[1]
        
        # Mapeo básico de mime_type a extensión
        mime_to_ext = {
            'image/jpeg': '.jpg',
            'image/png': '.png',
            'image/gif': '.gif',
            'image/webp': '.webp',
            'audio/mpeg': '.mp3',
            'audio/mp4': '.mp4',
            'audio/ogg': '.ogg',
            'video/mp4': '.mp4',
            'video/quicktime': '.mov',
            'application/pdf': '.pdf',
            'application/msword': '.doc',
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

        newChat = False

        if chat:
            chat.Estado = 1
            chat.nuevos_mensajes = chat.nuevos_mensajes + 1
            chat.save()
        else:
            chat = Whatsapp.objects.create(
                IDRedSocial=setting.IDRedSocial,
                Nombre=name,
                Telefono=phone,
                IDEL=find_state_id(2, 'No leído'),
                nuevos_mensajes=1,
                Estado=1
            )
            newChat = True

            # Push notification para nuevo chat
            if newChat:
                firebase_service = FirebaseServiceV1()
                tokens = get_user_tokens_by_permissions("messenger.index")
                if len(tokens) > 0:
                    firebase_service.send_to_multiple_devices(
                        tokens=tokens,
                        title="Nuevo mensaje en WhatsApp",
                        body=f"Nuevo mensaje de {name}",
                        data={'type': 'router', 'route_name': 'WhatsappPage'}
                    )

        return chat

    def _save_incoming_message(self, chat, phone, message_content, media_info=None, button_id=None):
        """
        Guarda mensaje entrante en la base de datos
        """
        Fecha, Hora = get_date_time()
        
        # Preparar URL y extensión si hay media
        url = None
        extension_data = None
        
        if media_info:
            url = media_info.get('local_path')
            
            # Actualizar path con teléfono correcto
            if url:
                url = url.replace('/temp/', f'/{phone}/')
                # Mover archivo a la carpeta correcta
                self._move_media_file(media_info, phone)
            
            # Crear datos de extensión como JSON
            extension_data = {
                'name': media_info.get('filename', 'archivo'),
                'size': media_info.get('size', 0),
                'type': media_info.get('mime_type', 'application/octet-stream'),
                'extension': media_info.get('filename', '').split('.')[-1] if media_info.get('filename') else '',
                'media_type': media_info.get('type'),
                'duration': media_info.get('duration')  # Para audio/video
            }
            
            # Campos específicos para audio
            if media_info.get('type') == 'audio':
                extension_data['audio'] = True
                extension_data['voice'] = media_info.get('voice', False)

        # Guardar mensaje
        mensaje_guardado = WhatsappMensajes.objects.create(
            IDChat=chat.IDChat,
            Telefono=phone,
            Mensaje=message_content,
            Fecha=Fecha,
            Hora=Hora,
            Url=url,
            Extencion=json.dumps(extension_data) if extension_data else None,
            Estado=2  # Mensaje recibido
        )

        # Actualizar timestamps del chat
        dateNative = get_naive_peru_time()
        chat.FechaUltimaPlantilla = dateNative
        chat.updated_at = dateNative 
        chat.save()

        # Marcar como vistos los mensajes anteriores
        WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat,
            Estado=1
        ).update(Estado=3)

        return mensaje_guardado

    def _move_media_file(self, media_info, phone):
        """
        Mueve el archivo de la carpeta temporal a la carpeta del teléfono
        """
        if not media_info or not media_info.get('filename'):
            return
            
        try:
            # Rutas
            temp_path = f"media/whatsapp/temp/{media_info['filename']}"
            final_path = f"media/whatsapp/{phone}/{media_info['filename']}"
            
            # Leer archivo de la ruta temporal
            from apps.users.views.wasabi import get_wasabi_file_data
            file_result = get_wasabi_file_data(f"{settings.MEDIA_URL.rstrip('/')}/whatsapp/temp/{media_info['filename']}")
            
            if file_result['success']:
                # Guardar en la nueva ubicación
                wasabi_result = save_file_to_wasabi(
                    file_result['file_data'],
                    final_path,
                    media_info.get('mime_type', 'application/octet-stream')
                )
                
                if wasabi_result['success']:
                    print(f"Archivo movido exitosamente a: {final_path}")
                    # Opcionalmente eliminar el archivo temporal
                    # self._delete_temp_file(temp_path)
                else:
                    print(f"Error moviendo archivo: {wasabi_result['error']}")
            
        except Exception as e:
            print(f"Error moviendo archivo de media: {e}")

    def _handle_auto_response(self, setting, chat, message_content):
        """
        Maneja respuestas automáticas y OpenAI
        """
        # Respuesta automática para nuevos chats
        if chat.nuevos_mensajes == 1:  # Nuevo chat
            template = MessengerPlantilla.objects.filter(
                marca_id=setting.marca_id, 
                estado=True, 
                tipo=1
            ).first()
            if template:
                self.send_message(setting, chat, template.mensaje)

        # OpenAI response
        if setting.openai and chat.openai:
            self.open_ai_response(setting, chat)

    def handle_button_response(self, setting, chat, button_id, message_content):
        """
        Maneja respuestas específicas de botones
        """
        if button_id == "Sí, deseo agendar":
            response_message = "¡Perfecto! Te ayudaré con el proceso de agendamiento. ¿Cuándo te gustaría programar tu cita?"
            self.send_message(setting, chat, response_message)
            
        elif button_id == "No deseo":
            response_message = "Entiendo. Si cambias de opinión, estaré aquí para ayudarte."
            self.send_message(setting, chat, response_message)

    def open_ai_response(self, setting, chat):
        """
        Genera respuesta usando OpenAI
        """
        ultimos_mensajes = list(WhatsappMensajes.objects.filter(
            IDChat=chat.IDChat
        ).order_by('-IDChatMensaje')[:4])
        ultimos_mensajes.reverse()
        
        messages = []
        
        for entry in ultimos_mensajes:
            role = "assistant" if entry.Telefono == setting.Telefono else "user"
            messages.append({"role": role, "content": entry.Mensaje})
        
        res = chatbot.get_response(setting.marca_id, messages)
        self.send_message(setting, chat, res, 2)

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
        response = view.post(drf_request)
        
        return response