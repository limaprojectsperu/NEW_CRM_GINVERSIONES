from django.urls import path
from .views.chat_interno import (
    ChatInternoList, ChatInternoMessages, ChatInternoDestroy,
    ChatInternoUpdateDate, ChatInternoUpdateLead,
    ChatInternoChatUpdate, ChatInternoCreate, ChatInternoMiembros
)
from .views.chat_interno_app import (
    ChatInternoSendView, ChatInternoEditMessage, ChatInternoDeleteMessage
)

urlpatterns = [
    # Chat interno API básica
    path('chat-interno/all',                       ChatInternoList.as_view()),
    path('chat-interno/message/<int:id>',          ChatInternoMessages.as_view()),
    path('chat-interno/delete/<int:id>',           ChatInternoDestroy.as_view()),
    path('chat-interno/update-date/<int:id>',      ChatInternoUpdateDate.as_view()),
    path('chat-interno/update-lead/<int:id>',      ChatInternoUpdateLead.as_view()),
    path('chat-interno/update-chat/<int:id>',      ChatInternoChatUpdate.as_view()),
    
    # Gestión de chats
    path('chat-interno/create',                    ChatInternoCreate.as_view()),
    path('chat-interno/miembros/<int:id>',         ChatInternoMiembros.as_view()),
    
    # Mensajería
    path('chat-interno/send-message',              ChatInternoSendView.as_view()),
    path('chat-interno/edit-message/<int:message_id>', ChatInternoEditMessage.as_view()),
    path('chat-interno/delete-message/<int:message_id>', ChatInternoDeleteMessage.as_view()),
]