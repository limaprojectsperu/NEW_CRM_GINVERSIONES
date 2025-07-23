from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappConfiguracionUser, WhatsapChatUser
from ..serializers import WhatsappConfiguracionUserSerializer, WhatsapChatUserSerializer

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

class WhatsapChatUserViewSet(viewsets.ViewSet):
    
    def show(self, request, pk=None):
        """GET /api/whatsapp-chat-user/{user_id}/ - Obtener configuraciones por usuario"""
        qs = WhatsapChatUser.objects.filter(user_id=pk).order_by('id')
        serializer = WhatsapChatUserSerializer(qs, many=True)
        return Response({'data': serializer.data})
    
    def update(self, request, pk=None):
        """PUT /api/whatsapp-chat-user/{user_id}/ - Actualizar configuraciones de usuario"""
        try:
            # Eliminar todas las chat existentes del usuario
            WhatsapChatUser.objects.filter(user_id=pk).delete()
            
            # Crear nuevas chat basadas en chatsSelect
            items = request.data.get('chatsSelect', [])
            
            for item in items:
                WhatsapChatUser.objects.create(
                    user_id=pk,
                    IDChat=item
                )
            
            return Response({'message': 'Cambio guardado con éxito.'})
            
        except Exception as e:
            return Response(
                {'error': 'Error al actualizar configuraciones'}, 
                status=status.HTTP_400_BAD_REQUEST
            )