import os
from django.utils import timezone
from django.conf import settings
from django.db import models
from django.core.files.storage import default_storage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ChatInterno, ChatInternoMensaje, ChatInternoMiembro
from apps.utils.datetime_func import get_naive_peru_time
from ...utils.pusher_client import pusher_client
from ..serializers import ChatInternoMiembroSerializer
from apps.utils.FirebaseServiceV1 import FirebaseServiceV1
from apps.utils.tokens_phone import get_users_tokens
from apps.users.views.wasabi import get_wasabi_file_data, save_file_to_wasabi

class ChatInternoSendView(APIView):
    """
    POST /api/chat-interno/send-message/
    Envía un mensaje al chat interno
    """

    def post(self, request):
        data = request.data
        
        # Validaciones básicas
        chat_id = data.get('IDChat')
        sender_id = data.get('IDSender')
        mensaje = data.get('Mensaje', '')
        
        if not chat_id or not sender_id:
            return Response({
                'message': 'IDChat e IDSender son requeridos',
                'status': 400,
            }, status=status.HTTP_400_BAD_REQUEST)

        # Verificar que el chat existe
        try:
            chat = ChatInterno.objects.get(IDChat=chat_id, Estado=1)
        except ChatInterno.DoesNotExist:
            return Response({
                'message': 'Chat no encontrado o inactivo',
                'status': 404,
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario es miembro del chat
        if not ChatInternoMiembro.objects.filter(
            chat_interno_id=chat_id, 
            user_id=sender_id
        ).exists():
            return Response({
                'message': 'Usuario no es miembro del chat',
                'status': 403,
            }, status=status.HTTP_403_FORBIDDEN)

        # Procesar archivo adjunto si existe
        file_url = self._process_file(request, chat_id, sender_id)
        
        # Guardar mensaje en base de datos
        mensaje_obj = self._save_message(request, file_url)
        
        # Actualizar contadores de mensajes no leídos para otros miembros
        self._update_unread_counters(chat_id, sender_id)
        
        # Actualizar fecha del chat
        chat.updated_at = get_naive_peru_time()
        chat.save()
        
        # Enviar notificación en tiempo real
        miembros = ChatInternoMiembro.objects.filter(chat_interno_id=chat_id).exclude(user_id=sender_id)
        serializer = ChatInternoMiembroSerializer(miembros, many=True)
        self._send_realtime_notification(chat, mensaje_obj, serializer.data)

        #push notification
        firebase_service = FirebaseServiceV1()
        tokens = get_users_tokens(miembros)
        if len(tokens) > 0:
            firebase_service.send_to_multiple_devices(
                tokens=tokens,
                title="Nuevo mensaje recibido",
                body=mensaje_obj.Mensaje,
                data={'type': 'router', 'route_name': 'ChatInternoPage'}
            )

        return Response({
            'message': 'Mensaje enviado con éxito.',
            'data': {
                'IDChatMensaje': mensaje_obj.IDChatMensaje,
                'IDChat': mensaje_obj.IDChat,
                'IDSender': mensaje_obj.IDSender,
                'Mensaje': mensaje_obj.Mensaje,
                'Fecha': mensaje_obj.Fecha,
                'Hora': mensaje_obj.Hora,
                'Url': mensaje_obj.Url,
                'Extencion': mensaje_obj.Extencion,
                'Estado': mensaje_obj.Estado,
                'editado': mensaje_obj.editado,
            },
            'status': 200,
        })

    def _process_file(self, request, chat_id, sender_id):
        """
        Procesa archivos adjuntos (subidos o desde URL) - VERSION MEJORADA
        """
        # Verificar si es URL de archivo local
        url_file = request.data.get('urlFile')
        if url_file:
            result = self._process_file_from_url(url_file)
            if result['success']:
                return url_file
            else:
                # Log del error si es necesario
                print(f"Error procesando archivo desde URL: {result['error']}")
                return None
        
        # Procesar archivo subido
        upload = request.FILES.get('file')
        if upload:
            return self._process_uploaded_file(upload, chat_id, sender_id)
        
        return None

    def _process_file_from_url(self, url_file):
        """
        Valida que el archivo de la URL existe usando get_wasabi_file_data unificado.
        """
        try:
            file_result = get_wasabi_file_data(url_file)
            
            if file_result['success']:
                return {
                    'success': True,
                    'url': url_file,
                    'source': file_result['source'],
                    'filename': file_result['filename'],
                    'content_type': file_result['content_type']
                }
            else:
                return {
                    'success': False,
                    'error': file_result['error'],
                    'source': file_result['source']
                }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error validando archivo: {str(e)}',
                'source': 'error'
            }

    def _process_uploaded_file(self, upload, chat_id, sender_id):
        """
        Guarda archivo subido en Wasabi - ACTUALIZADO
        """
        try:
            # Generar nombre único para el archivo
            timestamp = int(timezone.now().timestamp())
            extension = os.path.splitext(upload.name)[1] if upload.name else ''
            filename = f'{timestamp}{extension}'
            rel_path = f'media/chat_interno/archivos/{chat_id}/{filename}'
            
            # Leer el archivo
            upload.seek(0)
            file_data = upload.read()
            
            # Guardar archivo en Wasabi
            wasabi_result = save_file_to_wasabi(file_data, rel_path, upload.content_type)
            
            if wasabi_result['success']:
                # Construir URL de respuesta
                file_url = f"{settings.MEDIA_URL.rstrip('/')}/chat_interno/archivos/{chat_id}/{filename}"
                return file_url
            else:
                # Log del error si es necesario
                print(f"Error guardando archivo en Wasabi: {wasabi_result['error']}")
                return None
                
        except Exception as e:
            print(f"Error procesando archivo subido: {str(e)}")
            return None
            
    def _save_message(self, request, file_url=None):
        """
        Guarda el mensaje en la base de datos
        """
        data = request.data
        
        mensaje = ChatInternoMensaje.objects.create(
            IDChat=data.get('IDChat'),
            IDSender=str(data.get('IDSender')),  # Convertir a string según el modelo
            Mensaje=data.get('Mensaje', ''),
            Fecha=data.get('Fecha'),
            Hora=data.get('Hora'),
            Url=file_url,
            Extencion=data.get('Extencion', ''),
            Estado=1  # Enviado
        )
        
        return mensaje

    def _update_unread_counters(self, chat_id, sender_id):
        """
        Incrementa el contador de mensajes no leídos para otros miembros
        """
        ChatInternoMiembro.objects.filter(
            chat_interno_id=chat_id
        ).exclude(
            user_id=sender_id
        ).update(
            nuevos_mensajes=models.F('nuevos_mensajes') + 1
        )

    def _send_realtime_notification(self, chat, mensaje, miembros):
        """
        Envía notificación en tiempo real usando Pusher
        """
        try:
            pusher_client.trigger(
                'chat-interno-channel', 
                'new-message', 
                {
                    'IDChat': chat.IDChat,
                    'miembros': miembros,
                    'mensaje': {
                        'IDChatMensaje': mensaje.IDChatMensaje,
                        'IDChat': mensaje.IDChat,
                        'IDSender': mensaje.IDSender,
                        'Mensaje': mensaje.Mensaje,
                        'Fecha': mensaje.Fecha,
                        'Hora': mensaje.Hora,
                        'Url': mensaje.Url,
                        'Extencion': mensaje.Extencion,
                        'Estado': mensaje.Estado,
                    }
                }
            )
        except Exception as e:
            # Log del error, pero no fallar el envío del mensaje
            print(f"Error enviando notificación en tiempo real: {e}")


class ChatInternoEditMessage(APIView):
    """
    POST /api/chat-interno/edit-message/{message_id}/
    Edita un mensaje existente
    """
    def post(self, request, message_id):
        try:
            mensaje = ChatInternoMensaje.objects.get(IDChatMensaje=message_id)
        except ChatInternoMensaje.DoesNotExist:
            return Response({
                'message': 'Mensaje no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar que el usuario puede editar el mensaje
        if str(mensaje.IDSender) != str(request.data.get('IDSender')):
            return Response({
                'message': 'No tienes permisos para editar este mensaje'
            }, status=status.HTTP_403_FORBIDDEN)

        # Actualizar mensaje
        nuevo_mensaje = request.data.get('Mensaje', '')
        if nuevo_mensaje:
            mensaje.Mensaje = nuevo_mensaje
            mensaje.editado = True
            mensaje.fecha_edicion = timezone.now()
            mensaje.save()

        return Response({
            'message': 'Mensaje editado con éxito',
            'data': {
                'IDChatMensaje': mensaje.IDChatMensaje,
                'Mensaje': mensaje.Mensaje,
                'editado': mensaje.editado,
                'fecha_edicion': mensaje.fecha_edicion
            }
        })


class ChatInternoDeleteMessage(APIView):
    """
    POST /api/chat-interno/delete-message/{message_id}/
    Elimina (marca como eliminado) un mensaje
    """
    def post(self, request, message_id):
        try:
            mensaje = ChatInternoMensaje.objects.get(IDChatMensaje=message_id)
        except ChatInternoMensaje.DoesNotExist:
            return Response({
                'message': 'Mensaje no encontrado'
            }, status=status.HTTP_404_NOT_FOUND)

        # Verificar permisos (el remitente o admin del chat)
        sender_id = str(request.data.get('IDSender'))
        is_sender = str(mensaje.IDSender) == sender_id
        is_admin = ChatInternoMiembro.objects.filter(
            chat_interno_id=mensaje.IDChat,
            user_id=sender_id,
            rol='Administrador'
        ).exists()

        if not (is_sender or is_admin):
            return Response({
                'message': 'No tienes permisos para eliminar este mensaje'
            }, status=status.HTTP_403_FORBIDDEN)

        # Marcar como eliminado
        mensaje.Estado = 4  # Eliminado
        mensaje.save()

        return Response({
            'message': 'Mensaje eliminado con éxito'
        })