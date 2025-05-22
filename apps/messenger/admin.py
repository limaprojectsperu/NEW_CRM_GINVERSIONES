from django.contrib import admin
from .models import MessengerConfiguracion, Messenger, MessengerMensaje, MessengerPlantilla, EstadoLead, SubEstadoLead

# Register your models here.
admin.site.register(MessengerConfiguracion)
admin.site.register(Messenger)
admin.site.register(MessengerMensaje)
admin.site.register(MessengerPlantilla)
admin.site.register(EstadoLead)
admin.site.register(SubEstadoLead)
