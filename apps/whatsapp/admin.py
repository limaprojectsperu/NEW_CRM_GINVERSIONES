from django.contrib import admin
from .models import (
    WhatsappConfiguracion,
    Whatsapp,
    WhatsappMensajes,
    Niveles,
    ChatNiveles,
    WhatsappMetaPlantillas,
)

# Register your models here.
admin.site.register(WhatsappConfiguracion)
admin.site.register(Whatsapp)
admin.site.register(WhatsappMensajes)
admin.site.register(Niveles)
admin.site.register(ChatNiveles)
admin.site.register(WhatsappMetaPlantillas)
