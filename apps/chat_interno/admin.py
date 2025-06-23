from django.contrib import admin
from .models import ChatInterno, ChatInternoMensaje, ChatInternoMiembro

# Register your models here.
admin.site.register(ChatInterno)
admin.site.register(ChatInternoMensaje)
admin.site.register(ChatInternoMiembro)