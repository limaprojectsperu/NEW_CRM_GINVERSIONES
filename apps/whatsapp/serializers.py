from rest_framework import serializers
from .models import Whatsapp, WhatsappMensajes, WhatsappConfiguracion, ChatNiveles, Niveles
from apps.redes_sociales.models import Marca 

class WhatsappMensajesSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappMensajes
        fields = '__all__'

class WhatsappSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Whatsapp
        fields = '__all__'

class WhatsappSerializer(serializers.ModelSerializer):
    lastMessage = serializers.SerializerMethodField()

    class Meta:
        model = Whatsapp
        fields = [
            'IDChat', 'IDRedSocial', 'Nombre', 'Telefono',
            'FechaUltimaPlantilla', 'updated_at', 'Avatar',
            'IDEL', 'IDSubEstadoLead', 'Estado', 'nuevos_mensajes', 'openai',
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
    marca = serializers.SerializerMethodField()

    class Meta:
        model = WhatsappConfiguracion
        fields = '__all__'
    
    def get_marca(self, obj):
        try:
            marca = Marca.objects.get(id=obj.marca_id)
            return {
                'id': marca.id,
                'nombre': marca.nombre
            }
        except Marca.DoesNotExist:
            return None

class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveles
        fields = '__all__'

class ChatNivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatNiveles
        fields = '__all__'
