from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Messenger, MessengerMensaje, MessengerConfiguracion
from ..serializers import (
    MessengerSerializer,
    MessengerMensajeSerializer,
    MessengerConfiguracionSerializer
)

class MessengerList(APIView):
    """
    POST /api/messenger/all/{id}/
    """
    def post(self, request, id):
        IDEL = int(request.data.get('IDEL', -1))

        qs = Messenger.objects.filter(IDRedSocial=id, Estado=1)
        if IDEL > 0:
            qs = qs.filter(IDEL=IDEL)
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
        Messenger.objects.filter(IDChat=id).update(updated_at=timezone.now())
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
        Messenger.objects.filter(IDChat=payload.get('IDChat')).update(
            IDEL=IDEL,
        )
        return Response({'message': 'ok'})


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
            # Ajusta MEDIA_ROOT según tu configuración
            ruta = f'messenger/avatars/{int(timezone.now().timestamp())}_{fichero.name}'
            with open(f'{settings.MEDIA_ROOT}/{ruta}', 'wb+') as destino:
                for chunk in fichero.chunks():
                    destino.write(chunk)
            m.Avatar = ruta
            avatar_path = ruta

        m.save()
        return Response({'message': 'ok', 'data': avatar_path})
