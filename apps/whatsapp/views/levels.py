import os
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Niveles, WhatsappMensajes, ChatNiveles
from ..serializers import NivelSerializer
from apps.users.views.wasabi import upload_to_wasabi

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
        padre = int(request.query_params.get('IDNivelPadre', -1))
        nivel = int(request.query_params.get('Nivel', -1))

        qs = Niveles.objects.filter(IDEstado=1).order_by('-IDNivel')
        if padre > 0:
            qs = qs.filter(IDNivelPadre=padre)
        if nivel > 0:
            qs = qs.filter(Nivel=nivel)

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

        qs = Niveles.objects.all().order_by('-IDNivel')
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
            return Response({'data': serializer.data, 'message': 'Nivel registrado con éxito.'})
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
            return Response({'data': serializer.data, 'message': 'Nivel actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def updateState(self, request, pk=None):
        """
        Método update - Actualizar Estado
        """
        estado = Niveles.objects.get(IDNivel=pk)
        estado.IDEstado = request.data.get('IDEstado')
        estado.save()
        serializer = NivelSerializer(estado)
        return Response({"data": serializer.data, "message": "Estado actualizado con éxito."})

    def destroy(self, request, pk=None):
        """
        DELETE /api/level/<pk>/
        Marcar IDEstado = 0
        """
        Niveles.objects.filter(IDNivel=pk).update(IDEstado=0)
        return Response({'message': 'Nivel desactivado exitosamente.'})

    def save_image(self, request, pk=None):
        """
        POST /api/level/<pk>/save-image/
        Guarda archivo en Wasabi y actualiza URLImagen
        """
        nivel = Niveles.objects.get(IDNivel=pk)
        upload = request.FILES.get('URLImagen')
        URLImagen = None
        
        if upload:
            try:
                # Generar nombre de archivo usando timestamp
                extension = os.path.splitext(upload.name)[1]  # Obtener extensión
                filename = f'{int(timezone.now().timestamp())}{extension}'
                
                # Definir la ruta en Wasabi
                file_path = f'media/nivel/{filename}'
                
                # Subir archivo a Wasabi usando la función auxiliar
                saved_path = upload_to_wasabi(upload, file_path)
                
                # Generar URL para acceder al archivo
                nivel.URLImagen = f"/{file_path}"
                
                nivel.save()
                URLImagen = nivel.URLImagen
                
            except Exception as e:
                return Response({
                    'message': 'Error al subir imagen',
                    'error': str(e)
                }, status=500)

        return Response({'message': 'ok', 'data': URLImagen})
    
    def save_image_original_local(self, request, pk=None):
        """
        POST /api/level/<pk>/save-image/
        Guarda archivo en MEDIA_ROOT/media/nivel/ y actualiza URLImagen
        """
        nivel = Niveles.objects.get(IDNivel=pk)
        upload = request.FILES.get('URLImagen')
        URLImagen = None
        
        if upload:
            # Crear directorios si no existen
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
            nivel_dir = os.path.join(media_dir, 'nivel')
            os.makedirs(nivel_dir, exist_ok=True)

            # Generar nombre de archivo usando timestamp
            extension = os.path.splitext(upload.name)[1]  # Obtener extensión
            filename = f'{int(timezone.now().timestamp())}{extension}'
            ruta = f'media/nivel/{filename}'  # Ruta relativa
            full_path = os.path.join(settings.MEDIA_ROOT, ruta)
            
            # Guardar el archivo
            with open(full_path, 'wb+') as destino:
                for chunk in upload.chunks():
                    destino.write(chunk)
            
            # Crear la URL correcta con MEDIA_URL (asegurando una sola barra)
            nivel.URLImagen = f"{settings.MEDIA_URL.rstrip('/')}/nivel/{filename}"
            nivel.save()
            URLImagen = nivel.URLImagen

        return Response({'message': 'ok', 'data': URLImagen})
