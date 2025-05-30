from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import Marca
from ..serializers import (
    MarcaSerializer,
)

class BrandViewSet(viewsets.ViewSet):

    """GET /api/estado-lead/ devuelve solo where estado = 1"""
    def list(self, request):
        data = Marca.objects.filter(estado=1).order_by('id')
        serializer = MarcaSerializer(data, many=True)
        return Response({'data': serializer.data})