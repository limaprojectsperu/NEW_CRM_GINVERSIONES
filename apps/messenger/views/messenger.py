import os
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.utils.datetime_func  import get_naive_peru_time
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion
from ..serializers import (
    MessengerSerializer,
    MessengerMensajeSerializer,
    MessengerConfiguracionSerializer
)

class MessengerList(APIView):
    """
    POST /api/messengers/{id}/?IDEL=&IDSubEstadoLead=
    """
    def post(self, request, id):
        IDEL = int(request.data.get('IDEL', -1))
        IDSub = int(request.data.get('IDSubEstadoLead', -1))
        search_text = request.data.get('searchMessage', '').strip()

        qs = Messenger.objects.filter(IDRedSocial=id, Estado=1)
        if IDEL > 0:
            qs = qs.filter(IDEL=IDEL)
        if IDSub > 0:
            qs = qs.filter(IDSubEstadoLead=IDSub)

        if search_text:
            matching_messages = MessengerMensaje.objects.filter(
                Mensaje__icontains=search_text
            ).values_list('IDChat', flat=True).distinct()
            
            qs = qs.filter(IDChat__in=matching_messages)

        qs = qs.order_by('-updated_at')

        serializer = MessengerSerializer(qs, many=True)
        return Response({'data': serializer.data})


class MessengerMessages(APIView):
    """
    GET /api/messenger/message/{id}/
    """
    def get(self, request, id):
        msgs = MessengerMensaje.objects.filter(IDChat=id).order_by('IDChatMensaje')
        serializer = MessengerMensajeSerializer(msgs, many=True)
        # Marcar como vistos (2→3)
        MessengerMensaje.objects.filter(IDChat=id, Estado=2).update(Estado=3)
        Messenger.objects.filter(IDChat=id).update(nuevos_mensajes=0)
        return Response({'data': serializer.data})


class MessengerDestroy(APIView):
    """
    POST /api/messenger/delete/{id}/
    """
    def post(self, request, id):
        Messenger.objects.filter(IDChat=id).update(Estado=0)
        return Response({'message': 'ok'})


class MessengerUpdateDate(APIView):
    """
    POST /api/messenger/update-date/{id}/
    """
    def post(self, request, id):
        Messenger.objects.filter(IDChat=id).update(updated_at=get_naive_peru_time())
        return Response({'message': 'ok'})


class MessengerSettingList(APIView):
    """
    GET /api/messenger/setting/
    """
    def get(self, request):
        qs = MessengerConfiguracion.objects.all()
        serializer = MessengerConfiguracionSerializer(qs, many=True)
        return Response({'data': serializer.data})


class MessengerUpdateLead(APIView):
    """
    POST /api/messenger/update-lead/{id}/
    """
    def post(self, request, id):
        payload = request.data
        IDEL = payload.get('IDEL', {}).get('IDEL')
        IDSub = payload.get('IDSubEstadoLead', {}).get('IDSubEstadoLead')
        Messenger.objects.filter(IDChat=payload.get('IDChat')).update(
            IDEL=IDEL,
            IDSubEstadoLead=IDSub if IDSub is not None else None
        )
        return Response({'message': 'Estado actualizado con éxito.'})


class MessengerChatUpdate(APIView):
    """
    POST /api/messenger/update-chat/{id}/
    """
    def post(self, request, id):
        m = Messenger.objects.get(IDChat=id)
        m.Nombre = request.data.get('Nombre')
        avatar_path = None
        
        fichero = request.FILES.get('file')
        if fichero:
            # Create directory if it doesn't exist
            # Modificar la ruta para incluir 'media' en la estructura
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
            avatar_dir = os.path.join(media_dir, 'messenger', 'avatars')
            os.makedirs(avatar_dir, exist_ok=True)
            
            # Generate file path using only timestamp
            extension = os.path.splitext(fichero.name)[1]  # Get the file extension
            filename = f'{int(timezone.now().timestamp())}{extension}'
            ruta = f'media/messenger/avatars/{filename}'  # Añadir 'media/' al inicio de la ruta
            full_path = os.path.join(settings.MEDIA_ROOT, ruta)
            
            # Save the file
            with open(full_path, 'wb+') as destino:
                for chunk in fichero.chunks():
                    destino.write(chunk)
                    
            # Crear la URL correcta con MEDIA_URL
            m.Avatar = f"{settings.MEDIA_URL.rstrip('/')}/messenger/avatars/{filename}"
            avatar_path = m.Avatar
            
        m.save()
        return Response({'message': 'Perfil actualizado con éxito.', 'data': avatar_path})
    
