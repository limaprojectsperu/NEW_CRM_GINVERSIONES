from rest_framework import serializers
from .models import Whatsapp, WhatsappMensajes, WhatsappConfiguracion, ChatNiveles, Niveles, WhatsappMetaPlantillas, WhatsappPlantillaResumen, WhatsappConfiguracionUser, WhatsappProfileAccepts, Lead, WhatsapChatUser, WhatsapChatUserHistorial 
from apps.redes_sociales.models import Marca, EstadoLead, SubEstadoLead
from apps.users.models import Users 

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
    nombre_estado = serializers.SerializerMethodField()
    nombre_subestado = serializers.SerializerMethodField()

    class Meta:
        model = Whatsapp
        fields = [
            'IDChat', 'IDRedSocial', 'Nombre', 'Telefono',
            'FechaUltimaPlantilla', 'updated_at', 'Avatar',
            'IDEL', 'nombre_estado', 'lead_id',
            'IDSubEstadoLead', 'nombre_subestado',
            'fecha_agenda', 'user_id_agenda',
            'fecha_proxima_plantilla', 'user_id_proxima_plantilla', 'template_name', 'template_params',
            'Estado', 'nuevos_mensajes', 'openai',
            'respuesta_generada_openai', 'lastMessage'
        ]

    def get_lastMessage(self, obj):
        msg = (
            WhatsappMensajes.objects
            .filter(IDChat=obj.IDChat)
            .order_by('-IDChatMensaje')
            .first()
        )
        return WhatsappMensajesSerializer(msg).data if msg else None

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

class WhatsappAgendaSerializer(serializers.ModelSerializer):
    usuario_agenda = serializers.SerializerMethodField()
    nombre_estado = serializers.SerializerMethodField()
    nombre_subestado = serializers.SerializerMethodField()

    class Meta:
        model = Whatsapp
        fields = [
            'IDChat', 'IDRedSocial', 'Nombre', 'Telefono',
            'FechaUltimaPlantilla', 'updated_at', 'Avatar',
            'IDEL', 'nombre_estado', 'lead_id',
            'IDSubEstadoLead', 'nombre_subestado',
            'fecha_agenda', 'user_id_agenda', 'usuario_agenda',
            'fecha_proxima_plantilla', 'user_id_proxima_plantilla', 'template_name', 'template_params',
            'Estado', 'nuevos_mensajes', 'openai',
            'respuesta_generada_openai'
        ]
    def get_usuario_agenda(self, obj):
        if obj.user_id_agenda:
            try:
                data = Users.objects.get(co_usuario=obj.user_id_agenda)
                return data.name
            except Users.DoesNotExist:
                return None
        return None
    
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
    
class WhatsappSingleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Whatsapp
        fields = '__all__'

class WhatsappConfiguracionSerializer(serializers.ModelSerializer):
    marca = serializers.SerializerMethodField()

    class Meta:
        model = WhatsappConfiguracion
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
        
class WhatsappConfiguracionUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsappConfiguracionUser
        fields = '__all__'

class WhatsapChatUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = WhatsapChatUser
        fields = '__all__'

class WhatsapChatUserHistorialSerializer(serializers.ModelSerializer):
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = WhatsapChatUserHistorial
        fields = '__all__'

    def get_user_name(self, obj):
        try:
            user = Users.objects.get(co_usuario=obj.user_id)
            return user.name
        except Users.DoesNotExist:
            return None
        
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