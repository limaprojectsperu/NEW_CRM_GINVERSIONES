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
        """POST /api/perfiles/ - Crear o actualizar perfil según se envíe co_perfil"""
        data = request.data.copy()
        co_perfil = data.get('co_perfil', None)

        if co_perfil:
            # Si se envía co_perfil, intentamos actualizar; si no existe, lo creamos
            defaults = {
                'no_perfil': data.get('no_perfil'),
                'nc_perfil': data.get('nc_perfil'),
                'in_estado': data.get('in_estado', 1),  # Por defecto activo si no se envía
            }
            perfil_obj, created = Perfiles.objects.update_or_create(
                co_perfil=co_perfil,
                defaults=defaults
            )
            serializer = PerfilesSerializer(perfil_obj)
            if created:
                mensaje = 'Perfil registrado con éxito.'
            else:
                mensaje = 'Perfil actualizado con éxito.'
            return Response({'data': serializer.data, 'message': mensaje})

        # Si no se envía co_perfil, creamos uno nuevo
        serializer = PerfilesSerializer(data=data)
        if serializer.is_valid():
            nuevo_perfil = serializer.save(in_estado=1)  # Valor por defecto activo
            return Response({
                'data': PerfilesSerializer(nuevo_perfil).data,
                'message': 'Perfil registrado con éxito.'
            })
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
