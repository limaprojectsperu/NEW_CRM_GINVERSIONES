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

    def create(self, request):
        """POST /api/user-tokens/ - Crear o actualizar token según se envíe id"""
        data = request.data.copy()
        token_id = data.get('id', None)

        if token_id:
            defaults = {
                'user_id': data.get('user_id'),
                'token': data.get('token'),
                'platform': data.get('platform'),
                'state': data.get('state', 1),
            }
            token_obj, created = UserTokens.objects.update_or_create(
                id=token_id,
                defaults=defaults
            )
            serializer = UserTokensSerializer(token_obj)
            mensaje = 'Token registrado con éxito.' if created else 'Token actualizado con éxito.'
            return Response({'data': serializer.data, 'message': mensaje})

        serializer = UserTokensSerializer(data=data)
        if serializer.is_valid():
            nuevo_token = serializer.save(state=1)
            return Response({
                'data': UserTokensSerializer(nuevo_token).data,
                'message': 'Token registrado con éxito.'
            })
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