from django.urls import path
from .views.messenger import (
    MessengerList, MessengerMessages, MessengerDestroy,
    MessengerUpdateDate, MessengerSettingList,
    MessengerUpdateLead, MessengerChatUpdate
    )
from .views.messenger_app import MessengerSendView
from .views.webhooks_messenger import WebhookVerifyReceive
from .views.states import EstadoLeadViewSet, SubEstadoLeadViewSet

urlpatterns = [
    # messenger api
    path('messenger/all/<int:id>',            MessengerList.as_view()),
    path('messenger/message/<int:id>',        MessengerMessages.as_view()),
    path('messenger/delete/<int:id>',         MessengerDestroy.as_view()),
    path('messenger/update-date/<int:id>',    MessengerUpdateDate.as_view()),
    path('messenger/setting',                 MessengerSettingList.as_view()),
    path('messenger/update-lead/<int:id>',    MessengerUpdateLead.as_view()),
    path('messenger/update-chat/<int:id>',    MessengerChatUpdate.as_view()),

    # Meta api
    path('messenger-app/send-message', MessengerSendView.as_view()),
    path('webhooks-messenger/app/<int:IDRedSocial>', WebhookVerifyReceive.as_view()),

    # APIs para EstadoLead
    path('lead-estados-all', EstadoLeadViewSet.as_view({ 'get': 'listAll' })),
    path('lead-estado', EstadoLeadViewSet.as_view({
        'get': 'list',
        'post': 'create'
        }), name='estado-lead-list'),
    path('lead-estado/<int:pk>', EstadoLeadViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
        }), name='estado-lead-detail'),
    path('lead-estado/estado/<int:pk>', EstadoLeadViewSet.as_view({ 'put': 'updateState' })),
    
    # APIs para SubEstadoLead
    path('lead-subestados-all', SubEstadoLeadViewSet.as_view({ 'get': 'listAll' })),
    path('lead-subestado', SubEstadoLeadViewSet.as_view({
        'get': 'list',
        'post': 'create'
        }), name='subestado-lead-list'),
    path('lead-subestado/<int:pk>', SubEstadoLeadViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
        }), name='subestado-lead-detail'),
    path('lead-subestado/estado/<int:pk>', SubEstadoLeadViewSet.as_view({ 'put': 'updateState' })),
]
