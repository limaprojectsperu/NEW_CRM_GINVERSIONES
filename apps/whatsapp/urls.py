from django.urls import path
from .views.webhooks import WhatsappWebhookAPIView
from .views.whatsapp_app import WhatsappSendAPIView
from .views.whatsapp import (
    WhatsappListAll, WhatsappList, WhatsappStore, WhatsappShow, WhatsappSettingList,
    WhatsappUpdateLead, WhatsappUpdate, WhatsappUpdateDate, WhatsappDestroy
)
from .views.levels import NivelViewSet
from .views.whatsapp_level import ChatLevelShow, ChatLevelUpdate

nivel_list = NivelViewSet.as_view({
    'get':  'list',
    'post': 'create'
})
nivel_detail = NivelViewSet.as_view({
    'put':    'update',
    'delete': 'destroy'
})
nivel_save_image = NivelViewSet.as_view({
    'post': 'save_image'
})

urlpatterns = [
    # Meta api
    path('webhooks-whatsapp/app/<int:IDRedSocial>', WhatsappWebhookAPIView.as_view(), name='whatsapp-webhook'),
    path('whatsapp-app/send-message', WhatsappSendAPIView.as_view()),

    # whatsapp api
    path('whatsapp/all', WhatsappListAll.as_view(), name='whatsapp-list-all'),
    path('whatsapp/all/<int:id>', WhatsappList.as_view(), name='whatsapp-list'),
    path('whatsapp/store', WhatsappStore.as_view(),       name='whatsapp-store'),
    path('whatsapp/message/<int:id>', WhatsappShow.as_view(),   name='whatsapp-show'),
    path('whatsapp/setting', WhatsappSettingList.as_view()),
    path('whatsapp/update-lead/<int:id>',    WhatsappUpdateLead.as_view()),
    path('whatsapp/update-chat/<int:id>', WhatsappUpdate.as_view(),    name='whatsapp-update'),
    path('whatsapp/update-date/<int:id>', WhatsappUpdateDate.as_view(), name='whatsapp-update-date'),
    path('whatsapp/delete/<int:id>',      WhatsappDestroy.as_view(),    name='whatsapp-destroy'),

    # level
    path('level-all', NivelViewSet.as_view({'get': 'listAll'}), name='level-all'),
    path('level', nivel_list, name='level-list-create'),
    path('level/<int:pk>', nivel_detail, name='level-detail'),
    path('level/<int:pk>/save-image', nivel_save_image, name='level-save-image'),

    # level whatsapp
    path('whatsapp-level/show/<int:id>',   ChatLevelShow.as_view(),   name='chatlevel-show'),
    path('whatsapp-level/update/<int:id>', ChatLevelUpdate.as_view(), name='chatlevel-update'),

]
