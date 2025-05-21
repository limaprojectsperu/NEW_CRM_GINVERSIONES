from rest_framework import serializers
from .models import Messenger, MessengerMensaje, MessengerConfiguracion, EstadoLead, SubEstadoLead

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
            'Estado', 'lastMessage', 'nuevos_mensajes'
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
        

class EstadoLeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = EstadoLead
        fields = '__all__'

class SubEstadoLeadSerializer(serializers.ModelSerializer):
    estado_lead = EstadoLeadSerializer(source='IDEL', read_only=True) 
    id_estado_lead = serializers.PrimaryKeyRelatedField(
        queryset=EstadoLead.objects.all(),
        source='IDEL',
        write_only=True
    )

    class Meta:
        model = SubEstadoLead
        fields = '__all__'
