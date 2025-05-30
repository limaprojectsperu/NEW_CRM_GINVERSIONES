from rest_framework import serializers
from .models import Whatsapp, WhatsappMensajes, WhatsappConfiguracion, ChatNiveles, Niveles

class WhatsappMensajesSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappMensajes
        fields = '__all__'

class WhatsappSerializer(serializers.ModelSerializer):
    lastMessage = serializers.SerializerMethodField()

    class Meta:
        model = Whatsapp
        fields = [
            'IDChat', 'IDRedSocial', 'Nombre', 'Telefono',
            'FechaUltimaPlantilla', 'updated_at', 'Avatar',
            'IDEL', 'IDSubEstadoLead', 'Estado', 'nuevos_mensajes',
            'lastMessage'
        ]

    def get_lastMessage(self, obj):
        msg = (
            WhatsappMensajes.objects
            .filter(IDChat=obj.IDChat)
            .order_by('-IDChatMensaje')
            .first()
        )
        return WhatsappMensajesSerializer(msg).data if msg else None

class WhatsappConfiguracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappConfiguracion
        fields = '__all__'

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveles
        fields = '__all__'

class ChatNivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatNiveles
        fields = '__all__'
