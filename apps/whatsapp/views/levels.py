import os
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response

from ..models import Niveles, WhatsappMensajes, ChatNiveles
from ..serializers import NivelSerializer

class NivelViewSet(viewsets.ViewSet):
    """
    GET    /api/level-all/              -> listAll
    GET    /api/level/?IDNivelPadre=&Nivel=   -> list
    POST   /api/level/                  -> create
    PUT    /api/level/<pk>/             -> update
    DELETE /api/level/<pk>/             -> destroy
    POST   /api/level/<pk>/save-image/  -> save_image
    """

    def _count_new_messages_for_level(self, nivel_id):
        chat_ids = ChatNiveles.objects.filter(IDNivel=nivel_id).values_list('IDChat', flat=True)
        return WhatsappMensajes.objects.filter(IDChat__in=chat_ids, Estado=2).count()

    def _get_levels(self, item):
        if item.NivelFinal == 1:
            return self._count_new_messages_for_level(item.IDNivel)
        total = 0
        for hijo in Niveles.objects.filter(IDNivelPadre=item.IDNivel):
            total += self._get_levels(hijo)
        return total

    def listAll(self, request):
        """
        GET /api/level-all/
        Sólo niveles activos + newMessages
        """
        qs = Niveles.objects.filter(IDEstado=1)
        serializer = NivelSerializer(qs, many=True)
        data = serializer.data
        for obj, row in zip(qs, data):
            row['newMessages'] = self._get_levels(obj)
        return Response({'data': data})

    def list(self, request):
        """
        GET /api/level/?IDNivelPadre=&Nivel=
        Todos los niveles (sin filtrar Estado), aplicando filtros opcionales
        """
        padre = int(request.query_params.get('IDNivelPadre', -1))
        nivel = int(request.query_params.get('Nivel', -1))

        qs = Niveles.objects.all()
        if padre > 0:
            qs = qs.filter(IDNivelPadre=padre)
        if nivel > 0:
            qs = qs.filter(Nivel=nivel)

        serializer = NivelSerializer(qs, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """
        POST /api/level/
        Crear un nuevo nivel
        """
        serializer = NivelSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'ok'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        PUT /api/level/<pk>/
        Actualizar nombre, descripción, color, Estado
        """
        nivel = Niveles.objects.get(IDNivel=pk)
        serializer = NivelSerializer(nivel, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'ok'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        DELETE /api/level/<pk>/
        Marcar IDEstado = 0
        """
        Niveles.objects.filter(IDNivel=pk).update(IDEstado=0)
        return Response({'message': 'ok'})

    def save_image(self, request, pk=None):
        """
        POST /api/level/<pk>/save-image/
        Guarda archivo en MEDIA_ROOT/media/nivel/ y actualiza URLImagen
        """
        nivel = Niveles.objects.get(IDNivel=pk)
        upload = request.FILES.get('URLImagen')
        if upload:
            folder = os.path.join(settings.MEDIA_ROOT, 'media', 'nivel')
            os.makedirs(folder, exist_ok=True)

            ext      = os.path.splitext(upload.name)[1]
            filename = f"{int(timezone.now().timestamp())}{ext}"
            fullpath = os.path.join(folder, filename)

            with open(fullpath, 'wb+') as dest:
                for chunk in upload.chunks():
                    dest.write(chunk)

            # Actualizamos campo con la URL accesible
            nivel.URLImagen = os.path.join(settings.MEDIA_URL, 'nivel', filename)
            nivel.save()

        return Response({'message': 'ok'})
