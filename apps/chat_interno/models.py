from django.db import models
from apps.redes_sociales.models import Marca

# Create your models here.

class ChatInterno(models.Model):
    TIPO_CHAT_CHOICES = [
        (1, 'Individual'),
        (2, 'Grupo')
    ]
     
    IDChat      = models.AutoField(primary_key=True, db_column='IDChat')
    Nombre      = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True, db_column='updated_at')
    Avatar      = models.CharField(max_length=100, null=True, blank=True, db_column='Avatar')
    Estado      = models.IntegerField(default=1, null=True, blank=True, db_column='Estado')

    tipo_chat = models.IntegerField(choices=TIPO_CHAT_CHOICES, default=1, help_text='Tipo de chat')
    descripcion = models.TextField(max_length=500, null=True, blank=True, help_text='Descripción del chat/grupo')
    creado_por = models.IntegerField(db_column='creado_por')

    class Meta:
        db_table = 'chat_interno'
        verbose_name_plural = 'Chat Interno Chats'

    def __str__(self):
        return f"{self.Nombre} ({self.IDChat})"

class ChatInternoMiembro(models.Model):
    """Tabla intermedia para manejar miembros del chat con información adicional"""
    ROLES_CHOICES = [
        ('Administrador', 'Administrador'),
        ('Miembro', 'Miembro')
    ]
    
    chat_interno_id = models.ForeignKey(ChatInterno, on_delete=models.CASCADE, related_name='miembros_detalle')
    user_id = models.IntegerField(db_column='user_id')
    rol = models.CharField(max_length=40, choices=ROLES_CHOICES, default='Miembro')
    fecha_union = models.DateTimeField(auto_now_add=True)
    nuevos_mensajes = models.IntegerField(default=0, blank=True, db_column='nuevos_mensajes')
    IDEL = models.IntegerField(null=True, blank=True, db_column='IDEL', help_text='ID estado')
    
    class Meta:
        db_table = 'chat_interno_miembro'
        unique_together = [('chat_interno_id', 'user_id')]
        verbose_name_plural = 'Chat Interno Miembros'
    
    def __str__(self):
        return f"Usuario {self.user_id} en {self.chat_interno_id}, rol {self.rol}"

class ChatInternoMensaje(models.Model):
    ESTADO_CHOICES = [
        (1, 'Enviado'),
        (2, 'Entregado'),
        (3, 'Leído'),
        (4, 'Eliminado')
    ]

    IDChatMensaje = models.AutoField(primary_key=True, db_column='IDChatMensaje', help_text='Id del Mensaje')
    IDChat        = models.IntegerField(verbose_name='ID del Chat')
    IDSender      = models.CharField(max_length=50, null=True, blank=True, db_column='IDSender')
    Mensaje       = models.CharField(max_length=2000, null=True, blank=True, db_column='Mensaje', help_text='Mensaje')
    Fecha         = models.CharField(max_length=50, null=True, blank=True, db_column='Fecha', help_text='Fecha del Mensaje')
    Hora          = models.CharField(max_length=50, null=True, blank=True, db_column='Hora', help_text='Hora del Mensaje')
    Url           = models.CharField(max_length=150, null=True, blank=True, db_column='Url')
    Extencion     = models.CharField(max_length=200, null=True, blank=True, db_column='Extencion')
    Estado        = models.IntegerField(choices=ESTADO_CHOICES, default=1, db_column='Estado')
    editado       = models.BooleanField(default=False, help_text='Mensaje editado')
    fecha_edicion = models.DateTimeField(null=True, blank=True, help_text='Fecha de última edición')
    
    class Meta:
        db_table = 'chat_interno_mensaje'
        unique_together = (('IDChatMensaje', 'IDChat'),)
        verbose_name_plural = 'Chat Interno mensajes'
    
    def __str__(self):
        return f"Mensaje: {self.Mensaje} {self.IDChatMensaje} ({self.IDChat})"