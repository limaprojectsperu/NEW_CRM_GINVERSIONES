from rest_framework import serializers
from .models import Messenger, MessengerMensaje, MessengerConfiguracion

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
            'updated_at', 'Avatar', 'IDLead', 'IDEL',
            'Estado', 'lastMessage'
        ]

    def get_lastMessage(self, obj):
        from .models import MessengerMensaje
        msg = (MessengerMensaje.objects
               .filter(IDChat=obj.IDChat)
               .order_by('-IDChatMensaje')
               .first())
        return MessengerMensajeSerializer(msg).data if msg else None


class MessengerConfiguracionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengerConfiguracion
        fields = '__all__'
