from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import PerfilPermissions
from ..serializers import (
    PerfilPermissionsSerializer
)

class PerfilPermissionsViewSet(viewsets.ViewSet):
    """ViewSet para la tabla PerfilPermissions"""
    
    def list(self, request):
        """GET /api/perfil-permissions/ - Listar relaciones activas"""
        perfil_permissions = PerfilPermissions.objects.all().order_by('id')
        serializer = PerfilPermissionsSerializer(perfil_permissions, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """POST /api/perfil-permissions/ - Crear nueva relación"""
        serializer = PerfilPermissionsSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Relación registrada con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/perfil-permissions/{id}/ - Actualizar relación"""
        perfil_permission = get_object_or_404(PerfilPermissions, id=pk)
        serializer = PerfilPermissionsSerializer(perfil_permission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Relación actualizada con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """DELETE /api/perfil-permissions/{id}/ - Eliminar relación físicamente"""
        perfil_permission = get_object_or_404(PerfilPermissions, id=pk)
        perfil_permission.delete()
        return Response({"message": "Relación eliminada exitosamente."})