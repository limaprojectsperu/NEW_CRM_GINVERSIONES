from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import MessengerConfiguracion
from ..serializers import (
    MessengerConfiguracionSerializer
)

class MessengerConfiguracionViewSet(viewsets.ViewSet):
    """GET - devuelve solo where IDEstado = 1"""
    def list(self, request):
        qs = MessengerConfiguracion.objects.filter(Estado=1)
        serializer = MessengerConfiguracionSerializer(qs, many=True)
        return Response({'data': serializer.data})
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar 
        """
        estado = MessengerConfiguracion.objects.get(IDRedSocial=pk)
        serializer = MessengerConfiguracionSerializer(estado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Configuración actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    