from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import ChatNiveles, Niveles
from ..serializers import ChatNivelSerializer

class ChatLevelShow(APIView):
    """
    GET /api/chat-level/show/<int:id>/
    Devuelve todos los ChatNiveles para el nivel especificado.
    """
    def get(self, request, id):
        qs = ChatNiveles.objects.filter(IDNivel=id)
        serializer = ChatNivelSerializer(qs, many=True)
        return Response({'data': serializer.data})

class ChatLevelUpdate(APIView):
    """
    POST /api/chat-level/update/<int:id>/
    Reemplaza los ChatNiveles de un nivel y actualiza NivelFinal en Niveles.
    """
    def post(self, request, id):
        chats = request.data.get('chatsSelect', [])
        # Eliminar relaciones antiguas
        ChatNiveles.objects.filter(IDNivel=id).delete()
        # Crear nuevas relaciones
        objs = [ChatNiveles(IDNivel=id, IDChat=chat_id) for chat_id in chats]
        ChatNiveles.objects.bulk_create(objs)
        # Marcar NivelFinal según existencia de chats
        Niveles.objects.filter(IDNivel=id).update(NivelFinal=1 if len(chats) > 0 else 0)
        return Response({'message': 'Se guardó correctamente los cambios.'}, status=status.HTTP_200_OK)
