from rest_framework import viewsets, status
from rest_framework.response import Response
from ..models import WhatsappConfiguracionUser, WhatsapChatUser, WhatsapChatUserHistorial
from ..serializers import WhatsappConfiguracionUserSerializer, WhatsapChatUserSerializer, WhatsapChatUserHistorialSerializer

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
    
    def updateReassignUser(self, request, pk=None):
        """PUT /api/whatsapp-chat-user/{user_id}/ """
        user_id = request.data.get('user_id')
        
        obj, created = WhatsapChatUser.objects.update_or_create(
            IDChat=pk,
            defaults={'user_id': user_id}
        )

        WhatsapChatUserHistorial.objects.create(
            whatsapp_chat_user_id=obj,
            IDChat=pk,
            user_id=user_id
        )
        
        if created:
            message = 'Usuario asignado al chat con éxito.'
        else:
            message = 'Usuario reasignado con éxito.'
        
        return Response({'message': message})
    
    def update(self, request, pk=None):
        """PUT /api/whatsapp-chat-user/{user_id}/ - Actualizar configuraciones de usuario"""
        try:
            # Eliminar todas las chat existentes del usuario
            WhatsapChatUser.objects.filter(user_id=pk).delete()
            
            # Crear nuevas chat basadas en chatsSelect
            items = request.data.get('chatsSelect', [])
            
            for item in items:
                chat_user = WhatsapChatUser.objects.create(
                    IDChat=item,
                    user_id=pk
                )

                WhatsapChatUserHistorial.objects.create(
                    whatsapp_chat_user_id=chat_user,
                    IDChat=item,
                    user_id=pk
                )
            
            return Response({'message': 'Cambio guardado con éxito.'})
            
        except Exception as e:
            return Response(
                {'error': 'Error al actualizar configuraciones'}, 
                status=status.HTTP_400_BAD_REQUEST
            )

class WhatsapChatUserHistorialViewSet(viewsets.ViewSet):
    
    def show(self, request, pk=None):
        """GET /api/whatsapp-chat-user-historial/{whatsapp_chat_user_id}/ - Obtener configuraciones por usuario"""
        chat_user = WhatsapChatUser.objects.filter(IDChat=pk).first()
        
        if chat_user:
            qs = WhatsapChatUserHistorial.objects.filter(whatsapp_chat_user_id=chat_user.id).order_by('-id')
            serializer = WhatsapChatUserHistorialSerializer(qs, many=True)
            return Response({'data': serializer.data})
        
        return Response({'data': []})