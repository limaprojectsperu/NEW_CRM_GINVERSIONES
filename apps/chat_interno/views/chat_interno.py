import os
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.utils.datetime_func import get_naive_peru_time
from ..models import ChatInterno, ChatInternoMensaje, ChatInternoMiembro
from ..serializers import (
    ChatInternoSerializer,
    ChatInternoMensajeSerializer,
    ChatInternoMiembroSerializer
)
from apps.utils.find_states import find_state_id

class ChatInternoList(APIView):
    """
    POST /api/chat-interno/{id}/?IDEL=
    Lista los chats internos con filtros opcionales
    """
    def post(self, request):
        IDEL = int(request.data.get('IDEL', -1))
        tipo_chat = int(request.data.get('tipo_chat', 0))
        search_text = request.data.get('searchMessage', '').strip()
        user_id = request.data.get('user_id')  # Para filtrar chats donde el usuario es miembro

        qs = ChatInterno.objects.filter(Estado=1)
        
        if tipo_chat > 0:
            qs = qs.filter(tipo_chat=tipo_chat)

        # Filtrar por usuario si se proporciona
        if user_id:
            chats_miembro = ChatInternoMiembro.objects.filter(
                user_id=user_id
            )
            
            # Aplicar filtro por IDEL si se especificó
            if IDEL > 0:
                chats_miembro = chats_miembro.filter(IDEL=IDEL)
                
            # Obtener IDs de chats donde el usuario es miembro
            chat_ids = chats_miembro.values_list('chat_interno_id', flat=True)
            qs = qs.filter(IDChat__in=chat_ids)
        else:
            # Si no se especifica user_id pero sí IDEL, filtrar chats que tengan algún miembro con ese IDEL
            if IDEL > 0:
                chats_con_estado = ChatInternoMiembro.objects.filter(
                    IDEL=IDEL
                ).values_list('chat_interno_id', flat=True).distinct()
                qs = qs.filter(IDChat__in=chats_con_estado)

        # Búsqueda en mensajes
        if search_text:
            matching_messages = ChatInternoMensaje.objects.filter(
                Mensaje__icontains=search_text
            ).values_list('IDChat', flat=True).distinct()
            
            qs = qs.filter(IDChat__in=matching_messages)

        qs = qs.order_by('-updated_at')

        serializer = ChatInternoSerializer(qs, many=True)
        return Response({'data': serializer.data})


class ChatInternoMessages(APIView):
    """
    GET /api/chat-interno/message/{id}/
    Obtiene los mensajes de un chat específico
    """
    def get(self, request, id):
        msgs = ChatInternoMensaje.objects.filter(IDChat=id).order_by('IDChatMensaje')
        serializer = ChatInternoMensajeSerializer(msgs, many=True)
        
        # Marcar como leídos (1,2→3)
        ChatInternoMensaje.objects.filter(IDChat=id, Estado__in=[1, 2]).update(Estado=3)
        
        # Resetear contador de nuevos mensajes para el usuario actual
        user_id = request.headers.get('userid')
        if user_id:
            chat = ChatInternoMiembro.objects.filter(chat_interno_id=id, user_id=user_id).first()
            if chat:
                chat.nuevos_mensajes = 0
                if chat.IDEL == find_state_id(3, 'No leído'):
                    chat.IDEL = find_state_id(3, 'Leído')
                chat.save()
        
        return Response({'data': serializer.data})


class ChatInternoDestroy(APIView):
    """
    POST /api/chat-interno/delete/{id}/
    Desactiva un chat (cambia Estado a 0)
    """
    def post(self, request, id):
        ChatInterno.objects.filter(IDChat=id).update(Estado=0)
        return Response({'message': 'Chat desactivado correctamente'})


class ChatInternoUpdateDate(APIView):
    """
    POST /api/chat-interno/update-date/{id}/
    Actualiza la fecha de última actividad del chat
    """
    def post(self, request, id):
        ChatInterno.objects.filter(IDChat=id).update(updated_at=get_naive_peru_time())
        return Response({'message': 'Fecha actualizada correctamente'})


class ChatInternoUpdateLead(APIView):
    """
    POST /api/chat-interno/update-lead/{id}/
    Actualiza el estado del lead asociado al chat
    """
    def post(self, request, id):
        payload = request.data
        IDEL = payload.get('IDEL', {}).get('IDEL')
        user_id = payload.get('user_id')
        
        ChatInternoMiembro.objects.filter(chat_interno_id=id, user_id=user_id).update(
            IDEL=IDEL,
        )
        return Response({'message': 'Estado del lead actualizado con éxito.'})


class ChatInternoChatUpdate(APIView):
    """
    POST /api/chat-interno/update-chat/{id}/
    Actualiza información del chat (nombre, avatar, descripción)
    """
    def post(self, request, id):
        try:
            chat = ChatInterno.objects.get(IDChat=id)
        except ChatInterno.DoesNotExist:
            return Response({'message': 'Chat no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        # Actualizar campos básicos
        chat.Nombre = request.data.get('Nombre', chat.Nombre)
        chat.descripcion = request.data.get('descripcion', chat.descripcion)
        
        avatar_path = None
        
        # Procesar archivo de avatar si existe
        fichero = request.FILES.get('file')
        if fichero:
            # Crear directorio si no existe
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
            avatar_dir = os.path.join(media_dir, 'chat_interno', 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # Generar nombre de archivo con timestamp
            extension = os.path.splitext(fichero.name)[1]
            filename = f'{int(timezone.now().timestamp())}{extension}'
            ruta = f'media/chat_interno/avatars/{filename}'
            full_path = os.path.join(settings.MEDIA_ROOT, ruta)
            
            # Guardar el archivo
            with open(full_path, 'wb+') as destino:
                for chunk in fichero.chunks():
                    destino.write(chunk)
                    
            # Crear la URL correcta con MEDIA_URL
            chat.Avatar = f"{settings.MEDIA_URL.rstrip('/')}/chat_interno/avatars/{filename}"
            avatar_path = chat.Avatar
            
        chat.save()
        return Response({
            'message': 'Chat actualizado con éxito.', 
            'data': avatar_path
        })


class ChatInternoCreate(APIView):
    """
    POST /api/chat-interno/create/
    Crea un nuevo chat interno
    """
    def post(self, request):
        data = request.data

        hasChatInt = ChatInterno.objects.filter(creado_por=data.get('creado_por'), Nombre=data.get('Nombre')).first()
        if hasChatInt:
            return Response({
                'message': 'Ya existe un chat o grupo con el mismo nombre.',
                'data': None,
                'status': 400,
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Crear el chat
        chat = ChatInterno.objects.create(
            Nombre=data.get('Nombre'),
            tipo_chat=data.get('tipo_chat', 1),
            descripcion=data.get('descripcion', ''),
            creado_por=data.get('creado_por')
        )
        
        # Agregar miembros si se proporcionan
        miembros = data.get('miembros', [])
        for miembro_data in miembros:
            ChatInternoMiembro.objects.create(
                chat_interno_id=chat,
                user_id=miembro_data.get('user_id'),
                rol=miembro_data.get('rol', 'Miembro'),
                IDEL=find_state_id(3, 'No leído'),
            )
        
        serializer = ChatInternoSerializer(chat)
        return Response({
            'message': 'Chat creado con éxito',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)


class ChatInternoMiembros(APIView):
    """
    GET /api/chat-interno/miembros/{id}/
    Lista los miembros de un chat específico
    
    POST /api/chat-interno/miembros/{id}/
    Sincroniza los miembros del chat. El array enviado representa el estado final deseado:
    - Miembros no incluidos en el array serán eliminados
    - Miembros nuevos serán creados
    - Miembros existentes serán actualizados si es necesario
    
    Formato del request:
    {
        "miembros": [
            {"user_id": 1, "rol": "Admin"},
            {"user_id": 2, "rol": "Miembro"}
        ]
    }
    """
    
    def get(self, request, id):
        miembros = ChatInternoMiembro.objects.filter(chat_interno_id=id)
        serializer = ChatInternoMiembroSerializer(miembros, many=True)
        return Response({'data': serializer.data})
    
    def post(self, request, id):
        try:
            chat = ChatInterno.objects.get(IDChat=id)
        except ChatInterno.DoesNotExist:
            return Response({'message': 'Chat no encontrado'}, status=status.HTTP_404_NOT_FOUND)
        
        nuevos_miembros_data = request.data.get('miembros', [])
        
        # Obtener los IDs de usuarios que deberían estar en el chat
        user_ids_deseados = {miembro['user_id'] for miembro in nuevos_miembros_data}
        
        # Obtener miembros actuales del chat
        miembros_actuales = ChatInternoMiembro.objects.filter(chat_interno_id=chat)
        user_ids_actuales = {miembro.user_id for miembro in miembros_actuales}
        
        # Estadísticas para la respuesta
        miembros_creados = []
        miembros_actualizados = []
        miembros_eliminados_count = 0
        
        # 1. Eliminar miembros que no están en la lista nueva
        user_ids_a_eliminar = user_ids_actuales - user_ids_deseados
        if user_ids_a_eliminar:
            miembros_eliminados_count = ChatInternoMiembro.objects.filter(
                chat_interno_id=chat,
                user_id__in=user_ids_a_eliminar
            ).delete()[0]
        
        # 2. Crear o actualizar miembros
        for miembro_data in nuevos_miembros_data:
            user_id = miembro_data.get('user_id')
            rol = miembro_data.get('rol', 'Miembro')
            
            miembro, created = ChatInternoMiembro.objects.get_or_create(
                chat_interno_id=chat,
                user_id=user_id,
                defaults={'rol': rol}
            )
            
            if created:
                miembros_creados.append(miembro)
            else:
                # Actualizar rol si es diferente
                if miembro.rol != rol:
                    miembro.rol = rol
                    miembro.save()
                    miembros_actualizados.append(miembro)
        
        # Preparar respuesta
        mensaje_partes = []
        if miembros_creados:
            mensaje_partes.append(f"{len(miembros_creados)} miembros agregados")
        if miembros_actualizados:
            mensaje_partes.append(f"{len(miembros_actualizados)} miembros actualizados")
        if miembros_eliminados_count:
            mensaje_partes.append(f"{miembros_eliminados_count} miembros eliminados")
        
        mensaje = ", ".join(mensaje_partes) if mensaje_partes else "No se realizaron cambios"
        
        # Obtener todos los miembros actuales después de la sincronización
        miembros_finales = ChatInternoMiembro.objects.filter(chat_interno_id=chat)
        serializer = ChatInternoMiembroSerializer(miembros_finales, many=True)
        
        return Response({
            'message': f'Sincronización completada: {mensaje}',
            'data': serializer.data,
            'stats': {
                'creados': len(miembros_creados),
                'actualizados': len(miembros_actualizados),
                'eliminados': miembros_eliminados_count,
                'total_actual': len(miembros_finales)
            }
        })