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
    
    def listByProfile(self, request, pk=None):
        """GET /api/users/ - Listar usuarios activos"""
        users = Users.objects.filter(co_perfil=pk, in_estado=1).order_by('co_usuario')
        serializer = UsersSerializer(users, many=True)
        return Response({'data': serializer.data})
    
    def show(self, request, pk=None):
        """GET /api/users/ - usuario"""
        user = Users.objects.filter(co_usuario=pk).first()
        serializer = UsersSerializer(user)
        return Response({'data': serializer.data})

    def create(self, request):
        """POST /api/users/ - Crear o actualizar usuario según se envíe co_usuario"""
        data = request.data.copy()
        co_usuario = data.get('co_usuario', None)

        if co_usuario:
            defaults = {
                'co_compania': data.get('co_compania'),
                'co_sede': data.get('co_sede'),
                'co_persona': data.get('co_persona'),
                'co_perfil': data.get('co_perfil'),
                'prefijo': data.get('prefijo'),
                'imagen': data.get('imagen'),
                'co_ultimo_menu': data.get('co_ultimo_menu'),
                'no_iniciales': data.get('no_iniciales'),
                'nu_celular_trabajo': data.get('nu_celular_trabajo'),
                'has_chats': data.get('has_chats', 0),
                'name': data.get('name'),
                'email': data.get('email'),
                'password': data.get('password'),
                'remember_token': data.get('remember_token'),
                'password_app': data.get('password_app'),
                'token_app': data.get('token_app'),
                'co_usuario_modifica': data.get('co_usuario_modifica'),
                'fe_usuario_modifica': data.get('fe_usuario_modifica'),
                'in_estado': data.get('in_estado', 1),
            }
            usuario_obj, created = Users.objects.update_or_create(
                co_usuario=co_usuario,
                defaults=defaults
            )
            serializer = UsersSerializer(usuario_obj)
            mensaje = 'Usuario registrado con éxito.' if created else 'Usuario actualizado con éxito.'
            return Response({'data': serializer.data, 'message': mensaje})

        serializer = UsersSerializer(data=data)
        if serializer.is_valid():
            nuevo_usuario = serializer.save(in_estado=1)
            return Response({
                'data': UsersSerializer(nuevo_usuario).data,
                'message': 'Usuario registrado con éxito.'
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def update(self, request, pk=None):
        """PUT /api/users/{id}/ - Actualizar usuario"""
        user = get_object_or_404(Users, co_usuario=pk)
        serializer = UsersSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Usuario actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def updateOpenai(self, request, pk=None):
        """PUT /api/users/{id}/ - Actualizar openai"""
        user = get_object_or_404(Users, co_usuario=pk)
        user.openai = request.data.get('openai')
        user.save()
        serializer = UsersSerializer(user)
        return Response({"data": serializer.data, "message": "Usuario actualizado con éxito."})
    
    def destroy(self, request, pk=None):
        """DELETE /api/users/{id}/ - Eliminar usuario (cambiar estado)"""
        user = get_object_or_404(Users, co_usuario=pk)
        user.in_estado = 0  # Marcar como eliminado
        user.save()
        serializer = UsersSerializer(user)
        return Response({"data": serializer.data, "message": "Usuario desactivado exitosamente."})
