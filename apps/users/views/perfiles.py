from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Perfiles
from ..serializers import (
    PerfilesSerializer, 
)

class PerfilesViewSet(viewsets.ViewSet):
    """ViewSet para la tabla Perfiles"""
    
    def list(self, request):
        """GET /api/perfiles/ - Listar perfiles activos"""
        perfiles = Perfiles.objects.filter(in_estado=1).order_by('co_perfil')
        serializer = PerfilesSerializer(perfiles, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """POST /api/perfiles/ - Crear nuevo perfil"""
        serializer = PerfilesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(in_estado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Perfil registrado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/perfiles/{id}/ - Actualizar perfil"""
        perfil = get_object_or_404(Perfiles, co_perfil=pk)
        serializer = PerfilesSerializer(perfil, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Perfil actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """DELETE /api/perfiles/{id}/ - Eliminar perfil (cambiar estado)"""
        perfil = get_object_or_404(Perfiles, co_perfil=pk)
        perfil.in_estado = 0  # Marcar como eliminado
        perfil.save()
        serializer = PerfilesSerializer(perfil)
        return Response({"data": serializer.data, "message": "Perfil desactivado exitosamente."})
