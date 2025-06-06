from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Permissions
from ..serializers import (
    PermissionsSerializer, 
)

class PermissionsViewSet(viewsets.ViewSet):
    """ViewSet para la tabla Permissions"""
    
    def list(self, request):
        """GET /api/permissions/ - Listar permisos activos"""
        permissions = Permissions.objects.filter(state=1).order_by('id')
        serializer = PermissionsSerializer(permissions, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """POST /api/permissions/ - Crear o actualizar permiso según se envíe id"""
        data = request.data.copy()
        permiso_id = data.get('id', None)

        if permiso_id:
            defaults = {
                'name': data.get('name'),
                'description': data.get('description'),
                'state': data.get('state', 1),
            }
            permiso_obj, created = Permissions.objects.update_or_create(
                id=permiso_id,
                defaults=defaults
            )
            serializer = PermissionsSerializer(permiso_obj)
            mensaje = 'Permiso registrado con éxito.' if created else 'Permiso actualizado con éxito.'
            return Response({'data': serializer.data, 'message': mensaje})

        serializer = PermissionsSerializer(data=data)
        if serializer.is_valid():
            nuevo_permiso = serializer.save(state=1)
            return Response({
                'data': PermissionsSerializer(nuevo_permiso).data,
                'message': 'Permiso registrado con éxito.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/permissions/{id}/ - Actualizar permiso"""
        permission = get_object_or_404(Permissions, id=pk)
        serializer = PermissionsSerializer(permission, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Permiso actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """DELETE /api/permissions/{id}/ - Eliminar permiso (cambiar estado)"""
        permission = get_object_or_404(Permissions, id=pk)
        permission.state = 0  # Marcar como eliminado
        permission.save()
        serializer = PermissionsSerializer(permission)
        return Response({"data": serializer.data, "message": "Permiso desactivado exitosamente."})

