from django.contrib import admin
from .models import Marca, Users, UserTokens, Permissions, Perfiles, PerfilPermissions

# Register your models here.
admin.site.register(Marca)
admin.site.register(Users)
admin.site.register(UserTokens)
admin.site.register(Permissions)
admin.site.register(Perfiles)
admin.site.register(PerfilPermissions)