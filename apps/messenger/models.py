from django.db import models
from apps.redes_sociales.models import Marca

# Create your models here.
    
class MessengerConfiguracion(models.Model):
    IDRedSocial = models.IntegerField(primary_key=True, db_column='IDRedSocial', help_text='ID de la Red Social')
    IDSender     = models.CharField(max_length=50, null=True, blank=True, db_column='IDSender')
    marca_id     = models.IntegerField(default=1, null=True, blank=True, db_column='marca_id')
    Nombre       = models.CharField(max_length=50, null=True, blank=True, db_column='Nombre')
    Token        = models.CharField(max_length=255, null=True, blank=True, db_column='Token', help_text='Token')
    TokenHook    = models.CharField(max_length=50, null=True, blank=True, db_column='TokenHook')
    urlHook      = models.CharField(max_length=100, null=True, blank=True, db_column='urlHook')
    urlApi       = models.CharField(max_length=100, null=True, blank=True, db_column='urlApi', help_text='urlApi')
    logo         = models.CharField(max_length=150, null=True, blank=True, db_column='logo')
    Estado       = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='Estado')
    openai       = models.BooleanField(default=False) 

    class Meta:
        db_table = 'MessengerConfiguracion'
        verbose_name_plural = 'Messenger Configuracion'

    def __str__(self):
        return self.Nombre or f"Config {self.IDRedSocial}"

class Messenger(models.Model):
    IDChat      = models.AutoField(primary_key=True, db_column='IDChat')
    IDRedSocial = models.IntegerField(default=1, db_column='IDRedSocial')
    IDSender    = models.CharField(max_length=50, null=True, blank=True, db_column='IDSender')
    Nombre      = models.CharField(max_length=50, null=True, blank=True, db_column='Nombre')
    updated_at  = models.DateTimeField(null=True, blank=True, db_column='updated_at')
    Avatar      = models.CharField(max_length=100, null=True, blank=True, db_column='Avatar')
    IDEL        = models.IntegerField(null=True, blank=True, db_column='IDEL', help_text='ID estado')
    IDSubEstadoLead = models.IntegerField(null=True, blank=True, db_column='IDSubEstadoLead', help_text='ID sub estado')
    nuevos_mensajes = models.IntegerField(default=0, blank=True, db_column='nuevos_mensajes')
    Estado      = models.IntegerField(default=1, null=True, blank=True, db_column='Estado')
    openai      = models.BooleanField(default=True) 

    class Meta:
        db_table = 'Messenger'
        unique_together = (('IDChat', 'IDRedSocial'),)
        verbose_name_plural = 'Messenger Chats'

    def __str__(self):
        return f"{self.Nombre} ({self.IDChat})"

class MessengerMensaje(models.Model):
    IDChatMensaje = models.AutoField(primary_key=True, db_column='IDChatMensaje', help_text='Id del Mensaje')
    IDChat        = models.IntegerField(verbose_name='ID del Chat')
    IDSender      = models.CharField(max_length=50, null=True, blank=True, db_column='IDSender')
    Mensaje       = models.CharField(max_length=2000, null=True, blank=True, db_column='Mensaje', help_text='Mensaje')
    Fecha         = models.CharField(max_length=50, null=True, blank=True, db_column='Fecha', help_text='Fecha del Mensaje')
    Hora          = models.CharField(max_length=50, null=True, blank=True, db_column='Hora', help_text='Hora del Mensaje')
    Url           = models.CharField(max_length=150, null=True, blank=True, db_column='Url')
    Extencion     = models.CharField(max_length=200, null=True, blank=True, db_column='Extencion')
    Estado        = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='1: enviado, 2: recibido, 3: visto')
    origen = models.IntegerField(default=1, null=True, blank=True, db_column='origen', help_text='1: default, 2: openai')

    class Meta:
        db_table = 'MessengerMensaje'
        unique_together = (('IDChatMensaje', 'IDChat'),)
        verbose_name_plural = 'Messenger mensajes'
    
    def __str__(self):
        return f"Mensaje: {self.Mensaje} {self.IDChatMensaje} ({self.IDChat})"
    

