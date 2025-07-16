from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappMetaPlantillas, WhatsappPlantillaResumen
from ..serializers import (
    WhatsappMetaPlantillasSerializer,
    WhatsappPlantillaResumenSerializer,
)

class WhatsappMetaPlantillasViewSet(viewsets.ViewSet):

    """GET /api/whatsapp-meta-plantillas/ devuelve solo where estado = 1"""
    def list(self, request, pk):
        plantillas = WhatsappMetaPlantillas.objects.filter(marca_id=pk, estado=1).order_by('id')
        serializer = WhatsappMetaPlantillasSerializer(plantillas, many=True)
        return Response({'data': serializer.data})

class WhatsappPlantillaResumenViewSet(viewsets.ViewSet):

    """GET /api/whatsapp-plantilla-resumen/ devuelve solo where estado = 1"""
    def list(self, request):
        resumenes = WhatsappPlantillaResumen.objects.filter(estado=1).select_related('whatsapp_meta_plantillas_id').order_by('-id')
        serializer = WhatsappPlantillaResumenSerializer(resumenes, many=True)
        return Response({'data': serializer.data})
    