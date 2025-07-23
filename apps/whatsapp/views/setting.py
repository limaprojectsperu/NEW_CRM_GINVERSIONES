from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappConfiguracion, WhatsappConfiguracionUser
from ..serializers import (
    WhatsappConfiguracionSerializer
)

class WhatsappConfiguracionViewSet(viewsets.ViewSet):
    """GET - devuelve solo where IDEstado = 1"""
    def list(self, request):
        qs = WhatsappConfiguracion.objects.filter(Estado=1)
        serializer = WhatsappConfiguracionSerializer(qs, many=True)
        return Response({'data': serializer.data})

    def listUser(self, request, pk):
        """GET - devuelve el filtro user_id = pk"""
        whatsapp_ids_for_user = WhatsappConfiguracionUser.objects.filter(
            user_id=pk
         ).values_list('IDRedSocial', flat=True)

        qs = WhatsappConfiguracion.objects.filter(
            Estado=1,
            IDRedSocial__in=whatsapp_ids_for_user # '__in' permite filtrar por una lista de valores
        ).order_by('IDRedSocial') 

        serializer = WhatsappConfiguracionSerializer(qs, many=True)
        return Response({'data': serializer.data})
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar 
        """
        estado = WhatsappConfiguracion.objects.get(IDRedSocial=pk)
        serializer = WhatsappConfiguracionSerializer(estado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Configuración actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    