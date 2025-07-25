from django.db import models
from apps.users.models import Users
from django.utils import timezone

# Create your models here.

class WhatsappConfiguracion(models.Model):
    IDRedSocial = models.AutoField(primary_key=True, db_column='IDRedSocial', help_text='ID de la Red Social')
    marca_id    = models.IntegerField(db_column='marca_id')
    Telefono    = models.CharField(max_length=20, null=True, blank=True, db_column='Telefono', help_text='Telefono Asociado a la Red Social')
    Nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    Token       = models.CharField(max_length=255, null=True, blank=True, db_column='Token', help_text='Token')
    TokenHook   = models.CharField(max_length=50, null=True, blank=True, db_column='TokenHook', help_text='TokenHook')
    url_graph_v = models.CharField(max_length=100, null=True, blank=True, db_column='url_graph_v')
    urlApi      = models.CharField(max_length=100, null=True, blank=True, db_column='urlApi', help_text='urlApi')
    Template    = models.CharField(max_length=100, null=True, blank=True, db_column='Template')
    Language    = models.CharField(max_length=40, null=True, blank=True, db_column='Language')
    logo        = models.CharField(max_length=150, null=True, blank=True, db_column='logo')
    Estado      = models.IntegerField(default=1, db_column='Estado', help_text='Estado del telefono asociado')
    openai      = models.BooleanField(default=False) 
    openai_analizador = models.BooleanField(default=True) 
    responder_automaticamente = models.BooleanField(default=False) 
    responder_automaticamente_minutos = models.IntegerField(default=5, db_column='responder_automaticamente_minutos')
    enviar_quien_escribio = models.BooleanField(default=False) 
    contactar_leads = models.BooleanField(default=False) 

    class Meta:
        db_table = 'whatsapp_configuracion'
        verbose_name_plural = 'WhatsApp Configuracion'

    def __str__(self):
        return f"Id: {self.IDRedSocial} - {self.Nombre} - {self.Telefono}"

class WhatsappConfiguracionUser(models.Model):
    id = models.AutoField(primary_key=True)
    IDRedSocial = models.IntegerField()
    user_id = models.IntegerField()

    class Meta:
        db_table = 'whatsapp_configuracion_user'
        verbose_name_plural = 'WhatsApp Configuracion Usuario'
        
    def __str__(self):
        return f"WhatsApp {self.IDRedSocial} - Usuario {self.user_id}"

class Whatsapp(models.Model):
    IDChat               = models.AutoField(primary_key=True, db_column='IDChat')
    IDRedSocial          = models.IntegerField(default=1, db_column='IDRedSocial')
    Nombre               = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    Telefono             = models.CharField(max_length=50, null=True, blank=True, db_column='Telefono')
    FechaUltimaPlantilla = models.DateTimeField(null=True, blank=True, db_column='FechaUltimaPlantilla')
    created_at           = models.DateTimeField(auto_now_add=True)
    updated_at           = models.DateTimeField(null=True, blank=True, db_column='updated_at')
    Avatar               = models.CharField(max_length=100, null=True, blank=True, db_column='Avatar')
    IDEL                 = models.IntegerField(null=True, blank=True, db_column='IDEL', help_text='ID lead estado')
    IDSubEstadoLead      = models.IntegerField(null=True, blank=True, db_column='IDSubEstadoLead')
    nuevos_mensajes      = models.IntegerField(default=0, blank=True, db_column='nuevos_mensajes')
    fecha_agenda         = models.DateTimeField(null=True, blank=True, db_column='fecha_agenda')
    user_id_agenda       = models.IntegerField(null=True, blank=True, db_column='user_id_agenda')
    fecha_proxima_plantilla = models.DateTimeField(null=True, blank=True, db_column='fecha_proxima_plantilla')
    user_id_proxima_plantilla = models.IntegerField(null=True, blank=True, db_column='user_id_proxima_plantilla')
    Estado               = models.IntegerField(default=1, null=True, blank=True, db_column='Estado')
    openai               = models.BooleanField(default=True) 
    respuesta_generada_openai = models.BooleanField(default=False)

    class Meta:
        db_table = 'whatsapp'
        unique_together = (('IDChat', 'IDRedSocial'),)
        verbose_name_plural = 'WhatsApp Chats'

    def __str__(self):
        return f"{self.Nombre} ({self.IDChat}) - {self.Telefono}"

class WhatsappMensajes(models.Model):
    IDChatMensaje = models.AutoField(primary_key=True, db_column='IDChatMensaje', help_text='Id del Mensaje')
    IDChat        = models.IntegerField(verbose_name='ID del Chat', help_text='ID del Chat')
    Telefono      = models.CharField(max_length=50, null=True, blank=True, db_column='Telefono', help_text='Telefono del Emisor/Receptor del Mensaje')
    user_id       = models.IntegerField(null=True, blank=True, db_column='user_id')
    Mensaje       = models.CharField(max_length=2000, null=True, blank=True, db_column='Mensaje', help_text='Mensaje')
    Fecha         = models.CharField(max_length=50, null=True, blank=True, db_column='Fecha', help_text='Fecha del Mensaje')
    Hora          = models.CharField(max_length=50, null=True, blank=True, db_column='Hora', help_text='Hora del Mensaje')
    Url           = models.CharField(max_length=150, null=True, blank=True, db_column='Url')
    Extencion     = models.CharField(max_length=200, null=True, blank=True, db_column='Extencion')
    Estado        = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='Estado del mensaje, 1: enviado, 2: recibido, 3: visto')
    origen = models.IntegerField(default=1, null=True, blank=True, db_column='origen', help_text='1:enviados, 2: recibidos, 3: openai')
    created_at  = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'whatsapp_mensajes'
        unique_together = (('IDChatMensaje', 'IDChat'),)
        verbose_name_plural = 'WhatsApp mensajes'

    def __str__(self):
        return f"Mensaje: {self.Mensaje} {self.IDChatMensaje} ({self.IDChat})"

class WhatsapChatUser(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    IDChat  = models.IntegerField(db_column='IDChat')
    user_id = models.IntegerField(db_column='user_id')

    class Meta:
        db_table = 'whatsapp_chat_users'
        verbose_name = 'WhatsApp Chat Usuario'
        verbose_name_plural = 'WhatsApp Chats Usuarios'

    def __str__(self):
        return f"Chat {self.IDChat} - Usuario {self.user_id}"
    
class WhatsappProfileAccepts(models.Model):
    id = models.AutoField(primary_key=True)
    perfil_id = models.IntegerField()
    accepts = models.CharField(max_length=800, null=True, blank=True, db_column='accepts')

    class Meta:
        db_table = 'whatsapp_perfil_acepta'
        verbose_name_plural = 'WhatsApp Perfil Acepta'
        
    def __str__(self):
        return f"Perfil {self.perfil_id} - Acepta {self.accepts}"
    
class Niveles(models.Model):
    IDNivel      = models.AutoField(primary_key=True, db_column='IDNivel')
    IDNivelPadre = models.IntegerField(null=True, blank=True, db_column='IDNivelPadre')
    Nombre       = models.CharField(max_length=150, null=True, blank=True, db_column='Nombre')
    Descripcion  = models.CharField(max_length=200, null=True, blank=True, db_column='Descripcion')
    Color        = models.CharField(max_length=40, null=True, blank=True, db_column='Color')
    URLImagen    = models.CharField(max_length=150, null=True, blank=True, db_column='URLImagen')
    Nivel        = models.IntegerField(null=True, blank=True, db_column='Nivel', help_text='nivel 1 al 8')
    NivelFinal   = models.IntegerField(default=0, db_column='NivelFinal')
    IDEstado     = models.IntegerField(default=1, db_column='IDEstado')

    class Meta:
        db_table = 'niveles'
        verbose_name_plural = 'Niveles'

    def __str__(self):
        return f"{self.Nombre} - Nivel {self.Nivel}"


class ChatNiveles(models.Model):
    IDChat  = models.IntegerField(db_column='IDChat')
    IDNivel = models.IntegerField(db_column='IDNivel')

    class Meta:
        db_table = 'chat_niveles'
        unique_together = (('IDChat', 'IDNivel'),)
        verbose_name_plural = 'Chat Niveles'

    def __str__(self):
        return f"Chat {self.IDChat} - Nivel {self.IDNivel}"


class WhatsappMetaPlantillas(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id')
    marca_id    = models.IntegerField(db_column='marca_id')
    nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='nombre')
    descripcion = models.CharField(max_length=255, null=True, blank=True, db_column='descripcion')
    lenguaje    = models.CharField(max_length=40, null=True, blank=True, db_column='lenguaje')
    mensaje     = models.CharField(max_length=1000, null=True, blank=True, db_column='mensaje')
    media_url   = models.CharField(max_length=150, null=True, blank=True, db_column='media_url')
    variables   = models.IntegerField(null=True, blank=True, db_column='variables')
    nombre_variables = models.CharField(max_length=255, null=True, blank=True, db_column='nombre_variables')
    variables_obligatorio = models.CharField(max_length=50, null=True, blank=True, db_column='variables_obligatorio')
    usuario_index = models.IntegerField(null=True, blank=True, db_column='usuario_index')
    tipo        = models.CharField(max_length=40, null=True, blank=True, db_column='tipo')
    estado      = models.IntegerField(default=1, db_column='estado')

    class Meta:
        db_table = 'whatsapp_meta_plantillas'
        verbose_name_plural = 'WhatsApp Meta Plantillas'

    def __str__(self):
        return f"({self.lenguaje}) - {self.nombre} - Descripción: {self.descripcion}"
    
class WhatsappPlantillaResumen(models.Model):
    id          = models.AutoField(primary_key=True, db_column='id')
    whatsapp_meta_plantillas_id = models.ForeignKey(WhatsappMetaPlantillas, on_delete=models.PROTECT, db_column='whatsapp_meta_plantillas_id', related_name='plantillas')
    enviados    = models.IntegerField(null=True, blank=True, db_column='enviados')
    exitosos    = models.IntegerField(null=True, blank=True, db_column='exitosos')
    fallidos    = models.IntegerField(null=True, blank=True, db_column='fallidos')
    origen_datos = models.CharField(max_length=50, null=True, blank=True, db_column='origen_datos')
    estado      = models.IntegerField(default=1, db_column='estado')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'whatsapp_plantilla_resumen'
        verbose_name_plural = 'WhatsApp Plantillas Resumen'

    def __str__(self):
        return f"id: {self.id} - exitosos: {self.exitosos} - fallidos: {self.fallidos}"

    
class Lead(models.Model):
    id = models.AutoField(primary_key=True, db_column='id')
    fecha_registro = models.DateTimeField(db_column='fecha_registro', null=True, blank=True)
    fecha_asignacion = models.DateTimeField(db_column='fecha_asignacion', null=True, blank=True)
    codigo_solicitud = models.CharField(max_length=50, db_column='codigo_solicitud', null=True, blank=True)
    medio_captacion = models.CharField(max_length=200, db_column='medio_captacion', null=True, blank=True)
    marca = models.CharField(max_length=100, db_column='marca', null=True, blank=True)
    nombre_lead = models.CharField(max_length=255, db_column='nombre_lead', null=True, blank=True)
    usuario_asignado = models.CharField(max_length=100, db_column='usuario_asignado', null=True, blank=True)
    monto_solicitado = models.DecimalField(max_digits=10, decimal_places=2, db_column='monto_solicitado', null=True, blank=True)
    celular = models.CharField(max_length=20, db_column='celular', null=True, blank=True)
    propiedad_registros_publicos = models.BooleanField(db_column='propiedad_registros_publicos', null=True, blank=True)
    ocurrencia = models.CharField(max_length=255, db_column='ocurrencia', null=True, blank=True)
    condicion = models.CharField(max_length=200, db_column='condicion', null=True, blank=True)
    tipo_garantia = models.CharField(max_length=100, db_column='tipo_garantia', null=True, blank=True)
    departamento = models.CharField(max_length=100, db_column='departamento', null=True, blank=True)
    provincia = models.CharField(max_length=100, db_column='provincia', null=True, blank=True)
    distrito = models.CharField(max_length=100, db_column='distrito', null=True, blank=True)

    class Meta:
        db_table = 'leads' 
        verbose_name = 'Lead'
        verbose_name_plural = 'Leads'

    def __str__(self):
        return f"{self.nombre_lead} ({self.celular})"