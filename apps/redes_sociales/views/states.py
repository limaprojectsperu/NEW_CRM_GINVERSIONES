from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import EstadoLead, SubEstadoLead
from ..serializers import (
    EstadoLeadSerializer,
    SubEstadoLeadSingleSerializer,
    SubEstadoLeadSerializer,
)

class EstadoLeadViewSet(viewsets.ViewSet):
    """GET /api/estado-lead/ """
    def listAll(self, request, red_social, IDRedSocial):
        qs = EstadoLead.objects.filter(red_social=red_social)
        if IDRedSocial > 0:
            qs = qs.filter(IDRedSocial=IDRedSocial)
        qs = qs.order_by('-IDEL')

        serializer = EstadoLeadSerializer(qs, many=True)
        return Response({'data': serializer.data})

    """GET /api/estado-lead/ devuelve solo where IDEstado = 1"""
    def list(self, request, red_social, IDRedSocial):
        qs = EstadoLead.objects.filter(IDEstado=1, red_social=red_social)
        if IDRedSocial > 0:
            qs = qs.filter(IDRedSocial=IDRedSocial)
        qs = qs.order_by('IDEL')

        serializer = EstadoLeadSerializer(qs, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """
        Método store - Crear un nuevo EstadoLead
        """
        serializer = EstadoLeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(IDEstado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Estado registrado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar un EstadoLead existente
        """
        estado = EstadoLead.objects.get(IDEL=pk)
        serializer = EstadoLeadSerializer(estado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Estado actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def updateState(self, request, pk=None):
        """
        Método update - Actualizar Estado
        """
        estado = EstadoLead.objects.get(IDEL=pk)
        estado.IDEstado = request.data.get('IDEstado')
        estado.save()
        serializer = EstadoLeadSerializer(estado)
        return Response({"data": serializer.data, "message": "Estado actualizado con éxito."})
    
    def destroy(self, request, pk=None):
        """
        Método destroy - Cambiar IDEstado a 0 (no eliminar físicamente)
        """
        estado = EstadoLead.objects.get(IDEL=pk)
        estado.IDEstado = 0  # Marcar como eliminado
        estado.save()
        serializer = EstadoLeadSerializer(estado)
        return Response({"data": serializer.data, "message": "Estado desactivado exitosamente."})
    

class SubEstadoLeadViewSet(viewsets.ViewSet):
    """GET /api/subestado-lead/ """
    def listAll(self, request, red_social, IDRedSocial):
        qs = SubEstadoLead.objects.filter(red_social=red_social)
        if IDRedSocial > 0:
            qs = qs.filter(IDRedSocial=IDRedSocial)
        qs = qs.select_related('IDEL').order_by('-IDSubEstadoLead')

        serializer = SubEstadoLeadSerializer(qs, many=True)
        return Response({'data': serializer.data})

    """GET /api/subestado-lead/ devuelve solo where IDEstado = 1"""
    def list(self, request, red_social, IDRedSocial):
        qs = SubEstadoLead.objects.filter(IDEstado=1, red_social=red_social)
        if IDRedSocial > 0:
            qs = qs.filter(IDRedSocial=IDRedSocial)
        qs = qs.order_by('IDSubEstadoLead')

        serializer = SubEstadoLeadSingleSerializer(qs, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """
        Método store - Crear un nuevo SubEstadoLead
        """
        serializer = SubEstadoLeadSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(IDEstado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Sub estado registrado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """
        Método update - Actualizar un SubEstadoLead existente
        """
        subestado = SubEstadoLead.objects.get(IDSubEstadoLead=pk)
        serializer = SubEstadoLeadSerializer(subestado, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Sub estado actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def updateState(self, request, pk=None):
        """
        Método update - Actualizar SubEstado
        """
        subestado = SubEstadoLead.objects.get(IDSubEstadoLead=pk)
        subestado.IDEstado = request.data.get('IDEstado')
        subestado.save()
        serializer = SubEstadoLeadSerializer(subestado)
        return Response({"data": serializer.data, "message": "Sub estado actualizado con éxito."})
    
    def destroy(self, request, pk=None):
        """
        Método destroy - Cambiar IDEstado a 0 (no eliminar físicamente)
        """
        subestado = SubEstadoLead.objects.get(IDSubEstadoLead=pk)
        subestado.IDEstado = 0  # Marcar como eliminado
        subestado.save()
        serializer = SubEstadoLeadSerializer(subestado)
        return Response({"data": serializer.data, "message": "Sub estado desactivado exitosamente."})
