from rest_framework import viewsets, status
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from ..models import UserTokens
from ..serializers import (
    UserTokensSerializer, 
)

class UserTokensViewSet(viewsets.ViewSet):
    """ViewSet para la tabla UserTokens"""
    
    def list(self, request):
        """GET /api/user-tokens/ - Listar tokens activos"""
        tokens = UserTokens.objects.filter(state=1).order_by('id')
        serializer = UserTokensSerializer(tokens, many=True)
        return Response({'data': serializer.data})

    def create(self, request, *args, **kwargs):
        """
        POST /api/user-tokens/ - Crea un nuevo token si la combinación
        de user_id y token no existe.
        """
        data = request.data.copy()

        user_id = data.get('user_id')
        token = data.get('token')

        # 1. Validar que los campos esenciales estén presentes
        if not user_id or not token:
            return Response(
                {'message': 'Los campos user_id y token son obligatorios.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 2. Consultar si ya existe un registro con la misma combinación
        existing_token = UserTokens.objects.filter(user_id=user_id, token=token).first()

        if existing_token:
            # Si ya existe, retornar el existente y un mensaje de que ya estaba registrado
            serializer = UserTokensSerializer(existing_token)
            return Response(
                {'data': serializer.data, 'message': 'Este token para este usuario ya está registrado.'},
                status=status.HTTP_200_OK
            )
        else:
            # Si no existe, proceder a crear el nuevo registro
            serializer = UserTokensSerializer(data=data)
            if serializer.is_valid():
                # Puedes establecer el estado por defecto aquí si no lo haces en el modelo/serializer
                nuevo_token = serializer.save(state=data.get('state', 1))
                return Response(
                    {'data': UserTokensSerializer(nuevo_token).data, 'message': 'Token registrado con éxito.'},
                    status=status.HTTP_201_CREATED
                )
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
    def update(self, request, pk=None):
        """PUT /api/user-tokens/{id}/ - Actualizar token"""
        token = get_object_or_404(UserTokens, id=pk)
        serializer = UserTokensSerializer(token, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'data': serializer.data, 'message': 'Token actualizado con éxito.'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def destroy(self, request, pk=None):
        """DELETE /api/user-tokens/{id}/ - Eliminar token físicamente"""
        token = get_object_or_404(UserTokens, id=pk)
        token.delete()  # Esto eliminará el registro de la base de datos
        return Response({"message": "Token eliminado exitosamente."}, status=status.HTTP_204_NO_CONTENT)