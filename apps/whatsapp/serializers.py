from rest_framework import serializers
from .models import Whatsapp, WhatsappMensajes, WhatsappConfiguracion, ChatNiveles, Niveles, WhatsappMetaPlantillas, WhatsappPlantillaResumen, WhatsappConfiguracionUser, WhatsappProfileAccepts, Lead 
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
    
class WhatsappSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Whatsapp
        fields = '__all__'

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
        
class WhatsappConfiguracionUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappConfiguracionUser
        fields = '__all__'

class WhatsappProfileAcceptsSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappProfileAccepts
        fields = '__all__'
        
class NivelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Niveles
        fields = '__all__'

class ChatNivelSerializer(serializers.ModelSerializer):
    whatsapp = serializers.SerializerMethodField()

    class Meta:
        model = ChatNiveles
        fields = '__all__'

    def get_whatsapp(self, obj):
        try:
            whatsapp = Whatsapp.objects.get(IDChat=obj.IDChat)
            return WhatsappSingleSerializer(whatsapp).data
        except Whatsapp.DoesNotExist:
            return None
        
class WhatsappMetaPlantillasSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappMetaPlantillas
        fields = '__all__'

class WhatsappPlantillaResumenSerializer(serializers.ModelSerializer):
    whatsapp_meta_plantillas = serializers.SerializerMethodField()
    
    class Meta:
        model = WhatsappPlantillaResumen
        fields = '__all__'
    
    def get_whatsapp_meta_plantillas(self, obj):
        try:
            plantilla = WhatsappMetaPlantillas.objects.get(id=obj.whatsapp_meta_plantillas_id.id)
            return {
                'id': plantilla.id,
                'nombre': plantilla.nombre,
                'descripcion': plantilla.descripcion,
                'lenguaje': plantilla.lenguaje,
                'tipo': plantilla.tipo
            }
        except WhatsappMetaPlantillas.DoesNotExist:
            return None
        
class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = '__all__'