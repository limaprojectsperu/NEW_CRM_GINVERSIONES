from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappConfiguracionUser
from ..serializers import WhatsappConfiguracionUserSerializer

class WhatsappConfiguracionUserViewSet(viewsets.ViewSet):
    
    def show(self, request, pk=None):
        """GET /api/whatsapp-configuracion-user/{user_id}/ - Obtener configuraciones por usuario"""
        configuraciones = WhatsappConfiguracionUser.objects.filter(user_id=pk).order_by('id')
        serializer = WhatsappConfiguracionUserSerializer(configuraciones, many=True)
        return Response({'data': serializer.data})
    
    def update(self, request, pk=None):
        """PUT /api/whatsapp-configuracion-user/{user_id}/ - Actualizar configuraciones de usuario"""
        try:
            # Eliminar todas las configuraciones existentes del usuario
            WhatsappConfiguracionUser.objects.filter(user_id=pk).delete()
            
            # Crear nuevas configuraciones basadas en settingsSelect
            settings_select = request.data.get('settingsSelect', [])
            
            for item in settings_select:
                WhatsappConfiguracionUser.objects.create(
                    user_id=pk,
                    IDRedSocial=item
                )
            
            return Response({'message': 'Cambio guardado con éxito.'})
            
        except Exception as e:
            return Response(
                {'error': 'Error al actualizar configuraciones'}, 
                status=status.HTTP_400_BAD_REQUEST
            )