from django.contrib import admin
from .models import Marca, MessengerPlantilla, EstadoLead, SubEstadoLead

# Register your models here.
admin.site.register(Marca)
admin.site.register(MessengerPlantilla)
admin.site.register(EstadoLead)
admin.site.register(SubEstadoLead)