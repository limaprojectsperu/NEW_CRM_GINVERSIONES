from rest_framework import serializers
from .models import ChatInterno, ChatInternoMensaje, ChatInternoConfiguracion, ChatInternoMiembro
from apps.redes_sociales.models import Marca 

class ChatInternoMensajeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInternoMensaje
        fields = '__all__'


class ChatInternoMiembroSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInternoMiembro
        fields = '__all__'


class ChatInternoSerializer(serializers.ModelSerializer):
    lastMessage = serializers.SerializerMethodField()
    miembros = serializers.SerializerMethodField()
    total_miembros = serializers.SerializerMethodField()

    class Meta:
        model = ChatInterno
        fields = [
            'IDChat', 'IDRedSocial', 'Nombre', 'created_at', 'updated_at',
            'Avatar', 'IDEL', 'IDSubEstadoLead', 'Estado', 'tipo_chat',
            'descripcion', 'creado_por', 'lastMessage', 'miembros', 'total_miembros'
        ]

    def get_lastMessage(self, obj):
        msg = (ChatInternoMensaje.objects
               .filter(IDChat=obj.IDChat)
               .order_by('-IDChatMensaje')
               .first())
        return ChatInternoMensajeSerializer(msg).data if msg else None

    def get_miembros(self, obj):
        miembros = ChatInternoMiembro.objects.filter(chat_interno_id=obj.IDChat)
        return ChatInternoMiembroSerializer(miembros, many=True).data

    def get_total_miembros(self, obj):
        return ChatInternoMiembro.objects.filter(chat_interno_id=obj.IDChat).count()


class ChatInternoConfiguracionSerializer(serializers.ModelSerializer):
    marca = serializers.SerializerMethodField()

    class Meta:
        model = ChatInternoConfiguracion
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