from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappProfileAccepts
from ..serializers import WhatsappProfileAcceptsSerializer
from django.shortcuts import get_object_or_404 
from apps.users.models import Perfiles 

class WhatsappProfileAcceptsViewSet(viewsets.ViewSet):
    
    def show(self, request, pk=None):
        """GET /api/whatsapp-profile-accepts/{perfil_id}/ - Obtener configuración por perfil"""

        profile_accepts = get_object_or_404(WhatsappProfileAccepts, perfil_id=pk)
        serializer = WhatsappProfileAcceptsSerializer(profile_accepts)
        return Response({'data': serializer.data})
    
    def getProfileAccepts(self, request):
        """GET /api/whatsapp-profile-accepts-by-name - Obtener configuración por perfil"""

        perfil = get_object_or_404(Perfiles, no_perfil=request.data.get('name'))
        profile_accepts = get_object_or_404(WhatsappProfileAccepts, perfil_id=perfil.co_perfil) 
        serializer = WhatsappProfileAcceptsSerializer(profile_accepts)
        return Response({'data': serializer.data})

    def update(self, request, pk=None):
        """PUT /api/whatsapp-profile-accepts/{perfil_id}/ - Crear o actualizar configuración de perfil"""
        try:
            accepts_data = request.data.get('accepts', '')
            
            # Intentar obtener el registro existente
            profile_accepts, created = WhatsappProfileAccepts.objects.get_or_create(
                perfil_id=pk,
                defaults={'accepts': accepts_data}
            )
            
            # Si no fue creado, actualizar el campo accepts
            if not created:
                profile_accepts.accepts = accepts_data
                profile_accepts.save()
            
            serializer = WhatsappProfileAcceptsSerializer(profile_accepts)
            message = 'Configuración creada con éxito.' if created else 'Configuración actualizada con éxito.'
            
            return Response({
                'message': message,
                'data': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': 'Error al procesar la configuración del perfil'},
                status=status.HTTP_400_BAD_REQUEST
            )