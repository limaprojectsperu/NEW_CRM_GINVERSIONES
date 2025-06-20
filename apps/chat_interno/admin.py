from django.contrib import admin
from .models import ChatInterno, ChatInternoMensaje, ChatInternoConfiguracion, ChatInternoMiembro

# Register your models here.
admin.site.register(ChatInterno)
admin.site.register(ChatInternoMensaje)
admin.site.register(ChatInternoConfiguracion)
admin.site.register(ChatInternoMiembro)