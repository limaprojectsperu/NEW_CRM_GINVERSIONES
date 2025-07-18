from django.contrib import admin
from .models import (
    WhatsappConfiguracion,
    Whatsapp,
    WhatsappMensajes,
    Niveles,
    ChatNiveles,
    WhatsappMetaPlantillas,
    WhatsappPlantillaResumen,
    WhatsappConfiguracionUser,
    WhatsappProfileAccepts,
    WhatsapChatUser,
    Lead,
)

# Register your models here.
admin.site.register(WhatsappConfiguracion)
admin.site.register(Whatsapp)
admin.site.register(WhatsappMensajes)
admin.site.register(Niveles)
admin.site.register(ChatNiveles)
admin.site.register(WhatsappMetaPlantillas)
admin.site.register(WhatsappPlantillaResumen)
admin.site.register(WhatsappConfiguracionUser)
admin.site.register(WhatsappProfileAccepts)
admin.site.register(WhatsapChatUser)
admin.site.register(Lead)
