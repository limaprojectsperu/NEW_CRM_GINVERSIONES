from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappMetaPlantillas, WhatsappPlantillaResumen
from ..serializers import (
    WhatsappMetaPlantillasSerializer,
    WhatsappPlantillaResumenSerializer,
)

class WhatsappMetaPlantillasViewSet(viewsets.ViewSet):
    """GET /api/whatsapp-meta-plantillas-all/ """
    def listAll(self, request):
        plantillas = WhatsappMetaPlantillas.objects.all().order_by('-id')
        serializer = WhatsappMetaPlantillasSerializer(plantillas, many=True)
        return Response({'data': serializer.data})

    """GET /api/whatsapp-meta-plantillas/ devuelve solo where estado = 1"""
    def list(self, request):
        plantillas = WhatsappMetaPlantillas.objects.filter(estado=1).order_by('id')
        serializer = WhatsappMetaPlantillasSerializer(plantillas, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """
        Método store - Crear una nueva WhatsappMetaPlantillas
        """
        serializer = WhatsappMetaPlantillasSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(estado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Plantilla registrada con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar una WhatsappMetaPlantillas existente
        """
        try:
            plantilla = WhatsappMetaPlantillas.objects.get(id=pk)
            serializer = WhatsappMetaPlantillasSerializer(plantilla, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'data': serializer.data, 'message': 'Plantilla actualizada con éxito.'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except WhatsappMetaPlantillas.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    
    def updateState(self, request, pk=None):
        """
        Método update - Actualizar Estado
        """
        try:
            plantilla = WhatsappMetaPlantillas.objects.get(id=pk)
            plantilla.estado = request.data.get('estado')
            plantilla.save()
            serializer = WhatsappMetaPlantillasSerializer(plantilla)
            return Response({"data": serializer.data, "message": "Estado actualizado con éxito."})
        except WhatsappMetaPlantillas.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """
        Método destroy - Cambiar estado a 0 (no eliminar físicamente)
        """
        try:
            plantilla = WhatsappMetaPlantillas.objects.get(id=pk)
            plantilla.estado = 0  # Marcar como eliminado
            plantilla.save()
            serializer = WhatsappMetaPlantillasSerializer(plantilla)
            return Response({"data": serializer.data, "message": "Plantilla desactivada exitosamente."})
        except WhatsappMetaPlantillas.DoesNotExist:
            return Response({'error': 'Plantilla no encontrada'}, status=status.HTTP_404_NOT_FOUND)

class WhatsappPlantillaResumenViewSet(viewsets.ViewSet):

    """GET /api/whatsapp-plantilla-resumen/ devuelve solo where estado = 1"""
    def list(self, request):
        resumenes = WhatsappPlantillaResumen.objects.filter(estado=1).select_related('whatsapp_meta_plantillas_id').order_by('-id')
        serializer = WhatsappPlantillaResumenSerializer(resumenes, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """
        Método store - Crear un nuevo WhatsappPlantillaResumen
        """
        serializer = WhatsappPlantillaResumenSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(estado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Resumen registrado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar un WhatsappPlantillaResumen existente
        """
        try:
            resumen = WhatsappPlantillaResumen.objects.get(id=pk)
            serializer = WhatsappPlantillaResumenSerializer(resumen, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({'data': serializer.data, 'message': 'Resumen actualizado con éxito.'})
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except WhatsappPlantillaResumen.DoesNotExist:
            return Response({'error': 'Resumen no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    def updateState(self, request, pk=None):
        """
        Método update - Actualizar Estado
        """
        try:
            resumen = WhatsappPlantillaResumen.objects.get(id=pk)
            resumen.estado = request.data.get('estado')
            resumen.save()
            serializer = WhatsappPlantillaResumenSerializer(resumen)
            return Response({"data": serializer.data, "message": "Estado actualizado con éxito."})
        except WhatsappPlantillaResumen.DoesNotExist:
            return Response({'error': 'Resumen no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    
    def destroy(self, request, pk=None):
        """
        Método destroy - Cambiar estado a 0 (no eliminar físicamente)
        """
        try:
            resumen = WhatsappPlantillaResumen.objects.get(id=pk)
            resumen.estado = 0  # Marcar como eliminado
            resumen.save()
            serializer = WhatsappPlantillaResumenSerializer(resumen)
            return Response({"data": serializer.data, "message": "Resumen desactivado exitosamente."})
        except WhatsappPlantillaResumen.DoesNotExist:
            return Response({'error': 'Resumen no encontrado'}, status=status.HTTP_404_NOT_FOUND)
