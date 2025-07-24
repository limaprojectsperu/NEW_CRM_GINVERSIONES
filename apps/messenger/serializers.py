from rest_framework import serializers
from .models import Messenger, MessengerMensaje, MessengerConfiguracion
from apps.redes_sociales.models import Marca, EstadoLead, SubEstadoLead 

class MessengerMensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessengerMensaje
        fields = '__all__'


class MessengerSerializer(serializers.ModelSerializer):
    lastMessage = serializers.SerializerMethodField()
    nombre_estado = serializers.SerializerMethodField()
    nombre_subestado = serializers.SerializerMethodField()

    class Meta:
        model = Messenger
        fields = [
            'IDChat', 'IDRedSocial', 'IDSender', 'Nombre',
            'updated_at', 'Avatar', 'IDEL', 'nombre_estado',
            'IDSubEstadoLead', 'nombre_subestado',
            'Estado', 'lastMessage', 'nuevos_mensajes', 'openai',
            'respuesta_generada_openai'
        ]

    def get_lastMessage(self, obj):
        msg = (MessengerMensaje.objects
               .filter(IDChat=obj.IDChat)
               .order_by('-IDChatMensaje')
               .first())
        return MessengerMensajeSerializer(msg).data if msg else None

    def get_nombre_estado(self, obj):
        if obj.IDEL:
            try:
                estado = EstadoLead.objects.get(IDEL=obj.IDEL)
                return estado.Nombre
            except EstadoLead.DoesNotExist:
                return None
        return None

    def get_nombre_subestado(self, obj):
        if obj.IDSubEstadoLead:
            try:
                subestado = SubEstadoLead.objects.get(IDSubEstadoLead=obj.IDSubEstadoLead)
                return subestado.Nombre
            except SubEstadoLead.DoesNotExist:
                return None
        return None


class MessengerConfiguracionSerializer(serializers.ModelSerializer):
    marca = serializers.SerializerMethodField()

    class Meta:
        model = MessengerConfiguracion
        fields = '__all__'
        extra_kwargs = {
            'Token': {'write_only': True},
            'url_graph_v': {'write_only': True},
            'urlApi': {'write_only': True}
        }

    def get_marca(self, obj):
        try:
            marca = Marca.objects.get(id=obj.marca_id)
            return {
                'id': marca.id,
                'nombre': marca.nombre
            }
        except Marca.DoesNotExist:
            return None


