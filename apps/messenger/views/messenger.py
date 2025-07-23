import os
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.utils.datetime_func  import get_naive_peru_time
from ..models import Messenger, MessengerMensaje
from ..serializers import (
    MessengerSerializer,
    MessengerMensajeSerializer
)
from apps.utils.find_states import find_state_id
from apps.users.views.wasabi import upload_to_wasabi
from apps.utils.pagination import PostDataPagination

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

        # Paginacion
        paginator = PostDataPagination(default_page_size=20)
        paginated_qs = paginator.paginate_queryset(qs, request, view=self)
        serializer = MessengerSerializer(paginated_qs, many=True)
        
        return paginator.get_paginated_response(serializer.data)

class MessengerMessages(APIView):
    """
    GET /api/messenger/message/{id}/
    """
    def get(self, request, id):
        msgs = MessengerMensaje.objects.filter(IDChat=id).order_by('IDChatMensaje')
        serializer = MessengerMensajeSerializer(msgs, many=True)
        # Marcar como vistos (2→3)
        MessengerMensaje.objects.filter(IDChat=id, Estado=2).update(Estado=3)

        chat = Messenger.objects.filter(IDChat=id).first()
        if chat:
            chat.nuevos_mensajes = 0
            if chat.IDEL == find_state_id(1, 'No leído'):
                chat.IDEL = find_state_id(1, 'Leído')
            chat.save()
            
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

class MessengerUpdateOpenai(APIView):
    """
    POST /api/messenger/update-openai/{id}/
    """
    def post(self, request, id):
        Messenger.objects.filter(IDChat=id).update(openai=request.data.get('openai'))
        return Response({'message': 'ok'})

class MessengerUpdateGeneratedResponse(APIView):
    """
    POST /api/messenger/update-generated-response/{id}/
    """
    def post(self, request, id):
        Messenger.objects.filter(IDChat=id).update(respuesta_generada_openai=request.data.get('respuesta_generada_openai'))
        return Response({'message': 'ok'})
        
class MessengerUpdateLead(APIView):
    """
    POST /api/messenger/update-lead/{id}/
    """
    def post(self, request, id):
        payload = request.data
        IDEL = payload.get('IDEL', {}).get('IDEL')
        IDSub = payload.get('IDSubEstadoLead', {}).get('IDSubEstadoLead') if payload.get('IDSubEstadoLead') else None
        
        Messenger.objects.filter(IDChat=payload.get('IDChat')).update(
            IDEL=IDEL,
            IDSubEstadoLead=IDSub
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
            # Generar nombre de archivo usando timestamp
            extension = os.path.splitext(fichero.name)[1]  # Obtener extensión
            filename = f'{int(timezone.now().timestamp())}{extension}'
                
            # Definir la ruta en Wasabi
            file_path = f'media/messenger/avatars/{filename}'
                
            # Subir archivo a Wasabi usando la función auxiliar
            saved_path = upload_to_wasabi(fichero, file_path)

            # Generar URL para acceder al archivo
            m.Avatar = f"/{file_path}"
            avatar_path = m.Avatar
            
        m.save()
        return Response({'message': 'Perfil actualizado con éxito.', 'data': avatar_path})
    
