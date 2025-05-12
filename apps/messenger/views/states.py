from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import EstadoLead, SubEstadoLead
from ..serializers import (
    EstadoLeadSerializer,
    SubEstadoLeadSerializer,
)

class EstadoLeadListView(APIView):
    """GET /api/estado-lead/ devuelve solo where IDEstado = 1"""
    def get(self, request):
        leads = EstadoLead.objects.filter(IDEstado=1)
        serializer = EstadoLeadSerializer(leads, many=True)
        return Response({'data': serializer.data})

class SubEstadoLeadListView(APIView):
    """GET /api/subestado-lead/ devuelve solo where IDEstado = 1"""
    def get(self, request):
        subleads = SubEstadoLead.objects.filter(IDEstado=1)
        serializer = SubEstadoLeadSerializer(subleads, many=True)
        return Response({'data': serializer.data})

