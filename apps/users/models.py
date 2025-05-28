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

    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        
    def __str__(self):
        return self.name


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


class Permissions(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=255, null=True, blank=True)
    state = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'permissions'
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        
    def __str__(self):
        return self.name


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
        return self.no_perfil


class PerfilPermissions(models.Model):
    id = models.AutoField(primary_key=True)
    perfil_id = models.IntegerField()
    permission_id = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'perfil_permissions'
        verbose_name = 'Perfil Permiso'
        verbose_name_plural = 'Perfil Permisos'
        
    def __str__(self):
        return f"Perfil {self.perfil_id} - Permission {self.permission_id}"