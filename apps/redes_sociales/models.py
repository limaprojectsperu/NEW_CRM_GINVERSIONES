from django.db import models

# Create your models here.

class Marca(models.Model):
    nombre = models.CharField(max_length=200, null=True, blank=True)
    estado = models.BooleanField(default=True) 

    class Meta:
        db_table = 'marcas'
        verbose_name = 'Marca'
        verbose_name_plural = 'Marcas'

    def __str__(self):
        return f"Marca {self.id}: {self.nombre}"
    

class MessengerPlantilla(models.Model):
    mensaje = models.CharField(max_length=2000, null=True, blank=True)
    url = models.CharField(max_length=150, null=True, blank=True)
    extension = models.CharField(max_length=200, null=True, blank=True) 
    estado = models.BooleanField(default=True) 
    marca_id = models.ForeignKey(Marca, on_delete=models.PROTECT, db_column='marca_id', related_name='plantillas')
    tipo = models.IntegerField(default=0, blank=True, db_column='tipo', help_text='0: default, 1: entrada, 2: salida')
    red_social = models.IntegerField(default=1, blank=True, db_column='red_social', help_text='1: Messenger, 2: Whatsapp, 3: Chat Interno')

    class Meta:
        db_table = 'messenger_plantillas'
        verbose_name = 'Respuesta automática' 
        verbose_name_plural = 'Respuestas automáticas'

    def __str__(self):
        return f"Plantilla {self.id}: {self.mensaje}" if self.mensaje else f"Plantilla {self.id}: archivo"
    
    
class EstadoLead(models.Model):
    IDEL = models.AutoField(primary_key=True, db_column='IDEL')
    Nombre = models.CharField(max_length=100, null=True, blank=True, db_column='Nombre')
    Color = models.CharField(max_length=20, null=True, blank=True, db_column='Color')
    IDEstado = models.IntegerField(default=1, null=True, blank=True, db_column='IDEstado')
    red_social = models.IntegerField(default=1, blank=True, db_column='red_social', help_text='1: Messenger, 2: Whatsapp, 3: Chat Interno')
    IDRedSocial = models.IntegerField(null=True, blank=True, db_column='IDRedSocial', help_text='0: Chat Interno, 1+: IDRedSocial')
    id_crm = models.IntegerField(null=True, blank=True, db_column='id_crm', help_text='id externo')

    class Meta:
        db_table = 'EstadoLead'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.Nombre or f"EstadoLead {self.IDEL}"

class SubEstadoLead(models.Model):
    IDSubEstadoLead = models.AutoField(primary_key=True, db_column='IDSubEstadoLead')
    IDEL = models.ForeignKey(EstadoLead, on_delete=models.CASCADE, db_column='IDEL', related_name='subestados')
    Nombre = models.CharField(max_length=150, null=True, blank=True, db_column='Nombre')
    Color = models.CharField(max_length=20, null=True, blank=True, db_column='Color')
    IDEstado = models.IntegerField(default=1, null=True, blank=True, db_column='IDEstado')
    red_social = models.IntegerField(default=1, blank=True, db_column='red_social', help_text='1: Messenger, 2: Whatsapp, 3: Chat Interno')
    IDRedSocial = models.IntegerField(null=True, blank=True, db_column='IDRedSocial', help_text='0: Chat Interno, 1+: IDRedSocial')
    id_crm = models.IntegerField(null=True, blank=True, db_column='id_crm', help_text='id externo')

    class Meta:
        db_table = 'SubEstadoLead'
        verbose_name_plural = 'Sub Estados'

    def __str__(self):
        return self.Nombre or f"SubEstadoLead {self.IDSubEstadoLead}"