from rest_framework import serializers
from .models import Messenger, MessengerMensaje, MessengerConfiguracion
from apps.redes_sociales.models import Marca 

class MessengerMensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengerMensaje
        fields = '__all__'


class MessengerSerializer(serializers.ModelSerializer):
    lastMessage = serializers.SerializerMethodField()

    class Meta:
        model = Messenger
        # incluir aquí todos los campos de Messenger, incluido IDSubEstadoLead
        fields = [
            'IDChat', 'IDRedSocial', 'IDSender', 'Nombre',
            'updated_at', 'Avatar', 'IDEL', 'IDSubEstadoLead',
            'Estado', 'lastMessage', 'nuevos_mensajes', 'openai',
            'respuesta_generada_openai'
        ]

    def get_lastMessage(self, obj):
        from .models import MessengerMensaje
        msg = (MessengerMensaje.objects
               .filter(IDChat=obj.IDChat)
               .order_by('-IDChatMensaje')
               .first())
        return MessengerMensajeSerializer(msg).data if msg else None


class MessengerConfiguracionSerializer(serializers.ModelSerializer):
    marca = serializers.SerializerMethodField()

    class Meta:
        model = MessengerConfiguracion
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


