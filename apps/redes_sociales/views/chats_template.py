import os
from django.conf import settings
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import MessengerPlantilla
from ..serializers import MessengerPlantillaSingleSerializer, MessengerPlantillaSerializer

class MessengerPlantillaViewSet(viewsets.ViewSet):
    """GET /api/messenger-plantillas-all/ """
    def listAll(self, request, red_social):
        plantillas = MessengerPlantilla.objects.filter(red_social=red_social).select_related('marca_id').order_by('-id')
        serializer = MessengerPlantillaSerializer(plantillas, many=True)
        return Response({'data': serializer.data})
    
    """GET /api/messenger-plantilla/ devuelve solo where estado = True"""
    def list(self, request, pk, red_social):
        plantillas = MessengerPlantilla.objects.filter(marca_id=pk, estado=True, red_social=red_social).order_by('id')
        serializer = MessengerPlantillaSingleSerializer(plantillas, many=True)
        return Response({'data': serializer.data})
    
    def create(self, request):
        """
        Método store - Crear una nueva MessengerPlantilla
        """
        data = request.data.copy()
        archivo = request.FILES.get('archivo')  # Archivo opcional
        
        # Si hay archivo, procesarlo
        if archivo:
            # Crear directorios si no existen
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
            plantilla_dir = os.path.join(media_dir, 'messenger', 'plantillas')
            os.makedirs(plantilla_dir, exist_ok=True)
            
            # Generar nombre de archivo usando timestamp
            extension = os.path.splitext(archivo.name)[1]  # Obtener extensión
            filename = f'{int(timezone.now().timestamp())}{extension}'
            ruta = f'media/messenger/plantillas/{filename}'  # Ruta relativa
            full_path = os.path.join(settings.MEDIA_ROOT, ruta)
            
            # Guardar el archivo
            with open(full_path, 'wb+') as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)
            
            # Crear la URL correcta con MEDIA_URL
            data['url'] = f"{settings.MEDIA_URL.rstrip('/')}/messenger/plantillas/{filename}"
        
        serializer = MessengerPlantillaSerializer(data=data)
        if serializer.is_valid():
            serializer.save(estado=True)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Respuesta registrada con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar una MessengerPlantilla existente
        """
        try:
            plantilla = MessengerPlantilla.objects.get(pk=pk)
        except MessengerPlantilla.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        data = request.data.copy()
        archivo = request.FILES.get('archivo')  # Archivo opcional
        
        # Si hay nuevo archivo, procesarlo
        if archivo:
            # Eliminar archivo anterior si existe
            if plantilla.url:
                # Extraer el path del archivo anterior
                old_filename = os.path.basename(plantilla.url)
                old_path = os.path.join(settings.MEDIA_ROOT, 'media', 'messenger', 'plantillas', old_filename)
                if os.path.exists(old_path):
                    os.remove(old_path)
            
            # Crear directorios si no existen
            media_dir = os.path.join(settings.MEDIA_ROOT, 'media')
            plantilla_dir = os.path.join(media_dir, 'messenger', 'plantillas')
            os.makedirs(plantilla_dir, exist_ok=True)
            
            # Generar nombre de archivo usando timestamp
            extension = os.path.splitext(archivo.name)[1]  # Obtener extensión
            filename = f'{int(timezone.now().timestamp())}{extension}'
            ruta = f'media/messenger/plantillas/{filename}'  # Ruta relativa
            full_path = os.path.join(settings.MEDIA_ROOT, ruta)
            
            # Guardar el archivo
            with open(full_path, 'wb+') as destino:
                for chunk in archivo.chunks():
                    destino.write(chunk)
            
            # Crear la URL correcta con MEDIA_URL
            data['url'] = f"{settings.MEDIA_URL.rstrip('/')}/messenger/plantillas/{filename}"
        
        serializer = MessengerPlantillaSerializer(plantilla, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Respuesta actualizada con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def updateState(self, request, pk=None):
        """
        Método update - Actualizar estado de MessengerPlantilla
        """
        try:
            plantilla = MessengerPlantilla.objects.get(pk=pk)
        except MessengerPlantilla.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        plantilla.estado = request.data.get('estado', plantilla.estado)
        plantilla.save()
        serializer = MessengerPlantillaSerializer(plantilla)
        return Response({"data": serializer.data, "message": "Estado de respuesta actualizado con éxito."})
    
    def destroy(self, request, pk=None):
        """
        Método destroy - Cambiar estado a False (no eliminar físicamente)
        """
        try:
            plantilla = MessengerPlantilla.objects.get(pk=pk)
        except MessengerPlantilla.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)
        
        plantilla.estado = False  # Marcar como eliminado
        plantilla.save()
        serializer = MessengerPlantillaSerializer(plantilla)
        return Response({"data": serializer.data, "message": "Respuesta desactivada exitosamente."})
