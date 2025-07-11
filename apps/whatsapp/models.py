from django.db import models

# Create your models here.

class WhatsappConfiguracion(models.Model):
    IDRedSocial = models.AutoField(primary_key=True, db_column='IDRedSocial', help_text='ID de la Red Social')
    marca_id    = models.IntegerField(db_column='marca_id')
    Telefono    = models.CharField(max_length=20, null=True, blank=True, db_column='Telefono', help_text='Telefono Asociado a la Red Social')
    Nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    Token       = models.CharField(max_length=255, null=True, blank=True, db_column='Token', help_text='Token')
    TokenHook   = models.CharField(max_length=50, null=True, blank=True, db_column='TokenHook', help_text='TokenHook')
    urlHook     = models.CharField(max_length=100, null=True, blank=True, db_column='urlHook')
    urlApi      = models.CharField(max_length=100, null=True, blank=True, db_column='urlApi', help_text='urlApi')
    Template    = models.CharField(max_length=100, null=True, blank=True, db_column='Template')
    Language    = models.CharField(max_length=40, null=True, blank=True, db_column='Language')
    logo        = models.CharField(max_length=150, null=True, blank=True, db_column='logo')
    Estado      = models.IntegerField(default=1, db_column='Estado', help_text='Estado del telefono asociado')
    openai      = models.BooleanField(default=False) 
    openai_analizador = models.BooleanField(default=True) 

    class Meta:
        db_table = 'whatsapp_configuracion'
        verbose_name_plural = 'WhatsApp Configuracion'

    def __str__(self):
        return self.Nombre or f"Config {self.IDRedSocial}"


class Whatsapp(models.Model):
    IDChat               = models.AutoField(primary_key=True, db_column='IDChat')
    IDRedSocial          = models.IntegerField(default=1, db_column='IDRedSocial')
    Nombre               = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    Telefono             = models.CharField(max_length=50, null=True, blank=True, db_column='Telefono')
    FechaUltimaPlantilla = models.DateTimeField(null=True, blank=True, db_column='FechaUltimaPlantilla')
    updated_at           = models.DateTimeField(null=True, blank=True, db_column='updated_at')
    Avatar               = models.CharField(max_length=100, null=True, blank=True, db_column='Avatar')
    IDEL                 = models.IntegerField(null=True, blank=True, db_column='IDEL', help_text='ID lead estado')
    IDSubEstadoLead      = models.IntegerField(null=True, blank=True, db_column='IDSubEstadoLead')
    nuevos_mensajes      = models.IntegerField(default=0, blank=True, db_column='nuevos_mensajes')
    Estado               = models.IntegerField(default=1, null=True, blank=True, db_column='Estado')
    openai               = models.BooleanField(default=True) 

    class Meta:
        db_table = 'whatsapp'
        unique_together = (('IDChat', 'IDRedSocial'),)
        verbose_name_plural = 'WhatsApp Chats'

    def __str__(self):
        return f"{self.Nombre} ({self.IDChat})"


class WhatsappMensajes(models.Model):
    IDChatMensaje = models.AutoField(primary_key=True, db_column='IDChatMensaje', help_text='Id del Mensaje')
    IDChat        = models.IntegerField(verbose_name='ID del Chat', help_text='ID del Chat')
    Telefono      = models.CharField(max_length=50, null=True, blank=True, db_column='Telefono', help_text='Telefono del Emisor/Receptor del Mensaje')
    Mensaje       = models.CharField(max_length=2000, null=True, blank=True, db_column='Mensaje', help_text='Mensaje')
    Fecha         = models.CharField(max_length=50, null=True, blank=True, db_column='Fecha', help_text='Fecha del Mensaje')
    Hora          = models.CharField(max_length=50, null=True, blank=True, db_column='Hora', help_text='Hora del Mensaje')
    Url           = models.CharField(max_length=150, null=True, blank=True, db_column='Url')
    Extencion     = models.CharField(max_length=200, null=True, blank=True, db_column='Extencion')
    Estado        = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='Estado del mensaje, 1: enviado, 2: recibido, 3: visto')
    origen = models.IntegerField(default=1, null=True, blank=True, db_column='origen', help_text='1: default, 2: openai')

    class Meta:
        db_table = 'whatsapp_mensajes'
        unique_together = (('IDChatMensaje', 'IDChat'),)
        verbose_name_plural = 'WhatsApp mensajes'

    def __str__(self):
        return f"Mensaje: {self.Mensaje} {self.IDChatMensaje} ({self.IDChat})"


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
    nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='nombre')
    descripcion = models.CharField(max_length=255, null=True, blank=True, db_column='descripcion')
    lenguaje    = models.CharField(max_length=40, null=True, blank=True, db_column='lenguaje')
    media_url   = models.CharField(max_length=150, null=True, blank=True, db_column='media_url')
    tipo        = models.CharField(max_length=40, null=True, blank=True, db_column='tipo')
    estado      = models.IntegerField(default=1, db_column='estado')

    class Meta:
        db_table = 'whatsapp_meta_plantillas'
        verbose_name_plural = 'WhatsApp Meta Plantillas'

    def __str__(self):
        return f"{self.nombre} - {self.lenguaje}"