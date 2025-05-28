from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import Users
from ..serializers import (
    UsersSerializer, 
)

class UsersViewSet(viewsets.ViewSet):
    """ViewSet para la tabla Users"""
    
    def list(self, request):
        """GET /api/users/ - Listar usuarios activos"""
        users = Users.objects.filter(in_estado=1).order_by('co_usuario')
        serializer = UsersSerializer(users, many=True)
        return Response({'data': serializer.data})

    def create(self, request):
        """POST /api/users/ - Crear nuevo usuario"""
        serializer = UsersSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(in_estado=1)  # Por defecto activo
            return Response({'data': serializer.data, 'message': 'Usuario registrado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/users/{id}/ - Actualizar usuario"""
        user = get_object_or_404(Users, co_usuario=pk)
        serializer = UsersSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Usuario actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """DELETE /api/users/{id}/ - Eliminar usuario (cambiar estado)"""
        user = get_object_or_404(Users, co_usuario=pk)
        user.in_estado = 0  # Marcar como eliminado
        user.save()
        serializer = UsersSerializer(user)
        return Response({"data": serializer.data, "message": "Usuario desactivado exitosamente."})
