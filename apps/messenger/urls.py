from django.urls import path
from .views.messenger import (
    MessengerList, MessengerMessages, MessengerDestroy,
    MessengerUpdateDate, MessengerUpdateOpenai, MessengerUpdateGeneratedResponse,
    MessengerUpdateLead, MessengerChatUpdate
    )
from .views.messenger_app import MessengerSendView
from .views.webhooks_messenger import WebhookVerifyReceive
from .views.setting import MessengerConfiguracionViewSet

urlpatterns = [
    # APIs setting
    path('messenger/setting', MessengerConfiguracionViewSet.as_view({ 'get': 'list' })),
    path('messenger/setting/<int:pk>', MessengerConfiguracionViewSet.as_view({
        'put': 'update',
        })),

    # messenger api
    path('messenger/all/<int:id>',            MessengerList.as_view()),
    path('messenger/message/<int:id>',        MessengerMessages.as_view()),
    path('messenger/delete/<int:id>',         MessengerDestroy.as_view()),
    path('messenger/update-date/<int:id>',    MessengerUpdateDate.as_view()),
    path('messenger/update-openai/<int:id>',    MessengerUpdateOpenai.as_view()),
    path('messenger/update-generated-response/<int:id>',    MessengerUpdateGeneratedResponse.as_view()),
    path('messenger/update-lead/<int:id>',    MessengerUpdateLead.as_view()),
    path('messenger/update-chat/<int:id>',    MessengerChatUpdate.as_view()),

    # Meta api
    path('messenger-app/send-message', MessengerSendView.as_view()),
    path('webhooks-messenger/app/<int:IDRedSocial>', WebhookVerifyReceive.as_view()),

]
