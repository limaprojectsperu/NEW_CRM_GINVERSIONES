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
    url_graph_v  = models.CharField(max_length=100, null=True, blank=True, db_column='url_graph_v')
    urlApi       = models.CharField(max_length=100, null=True, blank=True, db_column='urlApi', help_text='urlApi')
    logo         = models.CharField(max_length=150, null=True, blank=True, db_column='logo')
    Estado       = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='Estado')
    openai       = models.BooleanField(default=False) 
    openai_analizador = models.BooleanField(default=True) 
    responder_automaticamente = models.BooleanField(default=False) 
    responder_automaticamente_minutos = models.IntegerField(default=5, db_column='responder_automaticamente_minutos')
    enviar_quien_escribio = models.BooleanField(default=False) 
    
    class Meta:
        db_table = 'MessengerConfiguracion'
        verbose_name_plural = 'Messenger Configuracion'

    def __str__(self):
        return f"Id: {self.IDRedSocial} - {self.Nombre}"

class Messenger(models.Model):
    IDChat      = models.AutoField(primary_key=True, db_column='IDChat')
    IDRedSocial = models.IntegerField(default=1, db_column='IDRedSocial')
    IDSender    = models.CharField(max_length=50, null=True, blank=True, db_column='IDSender')
    Nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(null=True, blank=True, db_column='updated_at')
    Avatar      = models.CharField(max_length=100, null=True, blank=True, db_column='Avatar')
    IDEL        = models.IntegerField(null=True, blank=True, db_column='IDEL', help_text='ID estado')
    IDSubEstadoLead = models.IntegerField(null=True, blank=True, db_column='IDSubEstadoLead', help_text='ID sub estado')
    nuevos_mensajes = models.IntegerField(default=0, blank=True, db_column='nuevos_mensajes')
    Estado      = models.IntegerField(default=1, null=True, blank=True, db_column='Estado')
    openai      = models.BooleanField(default=True) 
    respuesta_generada_openai = models.BooleanField(default=False)
    
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
    user_id       = models.IntegerField(null=True, blank=True, db_column='user_id')
    Mensaje       = models.CharField(max_length=2000, null=True, blank=True, db_column='Mensaje', help_text='Mensaje')
    Fecha         = models.CharField(max_length=50, null=True, blank=True, db_column='Fecha', help_text='Fecha del Mensaje')
    Hora          = models.CharField(max_length=50, null=True, blank=True, db_column='Hora', help_text='Hora del Mensaje')
    Url           = models.CharField(max_length=150, null=True, blank=True, db_column='Url')
    Extencion     = models.CharField(max_length=200, null=True, blank=True, db_column='Extencion')
    Estado        = models.IntegerField(default=1, null=True, blank=True, db_column='Estado', help_text='1: enviado, 2: recibido, 3: visto')
    origen = models.IntegerField(default=1, null=True, blank=True, db_column='origen', help_text='1:enviados, 2: recibidos, 3: openai')
    created_at  = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'MessengerMensaje'
        unique_together = (('IDChatMensaje', 'IDChat'),)
        verbose_name_plural = 'Messenger mensajes'
    
    def __str__(self):
        return f"Mensaje: {self.Mensaje} {self.IDChatMensaje} ({self.IDChat})"
    

