from django.db import models

# Create your models here.

class Users(models.Model):
    co_usuario = models.AutoField(primary_key=True)
    co_compania = models.IntegerField(null=True, blank=True)
    co_sede = models.IntegerField(null=True, blank=True)
    co_persona = models.IntegerField(null=True, blank=True)
    co_perfil = models.IntegerField(null=True, blank=True)
    prefijo = models.CharField(max_length=10, null=True, blank=True)
    imagen = models.CharField(max_length=255, null=True, blank=True)
    co_ultimo_menu = models.IntegerField(null=True, blank=True)
    no_iniciales = models.CharField(max_length=10, null=True, blank=True)
    nu_celular_trabajo = models.CharField(max_length=20, null=True, blank=True)
    has_chats = models.IntegerField(default=0)
    name = models.CharField(max_length=255, null=True, blank=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)
    remember_token = models.CharField(max_length=255, null=True, blank=True)
    password_app = models.CharField(max_length=255, null=True, blank=True)
    token_app = models.CharField(max_length=255, null=True, blank=True)
    co_usuario_modifica = models.IntegerField(null=True, blank=True)
    fe_usuario_modifica = models.DateTimeField(null=True, blank=True)
    in_estado = models.IntegerField(default=1)
    openai = models.BooleanField(default=False) 
    responder_automaticamente = models.BooleanField(default=False) 
    responder_automaticamente_minutos = models.IntegerField(default=5)

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return f"id: {self.co_usuario} - {self.name}"

class UserTokens(models.Model):
    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    token = models.CharField(max_length=200, null=True, blank=True)
    platform = models.CharField(max_length=50, null=True, blank=True)
    state = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'user_tokens'
        verbose_name = 'Usuario Token'
        verbose_name_plural = 'Usuario Tokens'

        
    def __str__(self):
        return f"Token for user {self.user_id} - {self.platform}"

class Perfiles(models.Model):
    co_perfil = models.AutoField(primary_key=True)
    no_perfil = models.CharField(max_length=255, null=True, blank=True)
    nc_perfil = models.CharField(max_length=255, null=True, blank=True)
    in_estado = models.IntegerField(default=1)

    class Meta:
        db_table = 'perfiles'
        verbose_name = 'Perfil'
        verbose_name_plural = 'Perfiles'
        
    def __str__(self):
        return f"id: {self.co_perfil} - {self.no_perfil}"
    
class Acceso(models.Model):
    acceso_id = models.CharField(max_length=8, primary_key=True, db_column='acceso_id')
    acceso = models.CharField(max_length=150, null=True, blank=True, db_column='acceso')
    icono = models.CharField(max_length=50, null=True, blank=True, db_column='icono')
    estado = models.BooleanField(default=True) 
    
    class Meta:
        db_table = 'accesos'
        managed = True
        verbose_name = 'Acceso'
        verbose_name_plural = 'Accesos'
    
    def __str__(self):
        return f"{self.acceso_id} - {self.acceso}"

class AccesoPerfil(models.Model):
    acceso_id = models.ForeignKey(Acceso, on_delete=models.PROTECT, db_column='acceso_id', to_field='acceso_id')
    perfil_id = models.IntegerField(db_column='perfil_id')
    
    class Meta:
        db_table = 'acceso_perfiles'
        unique_together = ('acceso_id', 'perfil_id')
        managed = True
        verbose_name = 'Acceso Perfil'
        verbose_name_plural = 'Accesos Perfiles'
    
    def __str__(self):
        return f"acceso: {self.acceso_id} - perfil: {self.perfil_id}"