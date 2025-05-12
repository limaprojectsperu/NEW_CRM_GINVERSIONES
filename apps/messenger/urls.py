from django.urls import path
from .views.messenger import (
    MessengerList, MessengerMessages, MessengerDestroy,
    MessengerUpdateDate, MessengerSettingList,
    MessengerUpdateLead, MessengerChatUpdate
)
from .views.messenger_app import MessengerSendView
from .views.webhooks_messenger import WebhookVerify, WebhookReceive
from .views.states import EstadoLeadListView, SubEstadoLeadListView

urlpatterns = [
    path('messenger/all/<int:id>',            MessengerList.as_view()),
    path('messenger/message/<int:id>',        MessengerMessages.as_view()),
    path('messenger/delete/<int:id>',         MessengerDestroy.as_view()),
    path('messenger/update-date/<int:id>',    MessengerUpdateDate.as_view()),
    path('messenger/setting',                 MessengerSettingList.as_view()),
    path('messenger/update-lead/<int:id>',    MessengerUpdateLead.as_view()),
    path('messenger/update-chat/<int:id>',    MessengerChatUpdate.as_view()),

    path('messenger-app/send-message', MessengerSendView.as_view()),

    path('webhooks-messenger/app/<int:IDRedSocial>', WebhookVerify.as_view()),
    path('webhooks-messenger/app/<int:IDRedSocial>', WebhookReceive.as_view()),

    path('lead-status/all', EstadoLeadListView.as_view()),
    path('lead-substatus/all', SubEstadoLeadListView.as_view()),
]
