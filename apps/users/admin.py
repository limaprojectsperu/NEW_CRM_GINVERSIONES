from django.contrib import admin
from .models import Users, UserTokens, Permissions, Perfiles, PerfilPermissions, Acceso, AccesoPerfil

# Register your models here.
admin.site.register(Users)
admin.site.register(UserTokens)
admin.site.register(Permissions)
admin.site.register(Perfiles)
admin.site.register(PerfilPermissions)
admin.site.register(Acceso)
admin.site.register(AccesoPerfil)