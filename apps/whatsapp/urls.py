from django.urls import path
from .views.webhooks import WhatsappWebhookAPIView
from .views.whatsapp_app import WhatsappSendAPIView
from .views.whatsapp import (
    WhatsappListAll, WhatsappList, WhatsappAgendaList, WhatsappStore, WhatsappShow,
    WhatsappUpdateLead, WhatsappUpdate, WhatsappUpdateDate, WhatsappUpdateAgenda,
    WhatsappUpdateOpenai, WhatsappUpdateGeneratedResponse, WhatsappDestroy
)
from .views.levels import NivelViewSet
from .views.whatsapp_level import ChatLevelShow, ChatLevelUpdate
from .views.whatsapp_bulk import WhatsappBulkSendAPIView
from .views.summary_template import WhatsappMetaPlantillasViewSet, WhatsappPlantillaResumenViewSet
from .views.whatsapp_user import WhatsappConfiguracionUserViewSet, WhatsapChatUserViewSet
from .views.whatsapp_profile_accepts import WhatsappProfileAcceptsViewSet
from .views.lead import LeadViewSet
from .views.setting import WhatsappConfiguracionViewSet

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
    # APIs setting
    path('whatsapp/setting', WhatsappConfiguracionViewSet.as_view({ 'get': 'list' })),
    path('whatsapp/setting/<int:pk>', WhatsappConfiguracionViewSet.as_view({
        'get': 'listUser',
        'put': 'update',
        })),

    # Meta api
    path('webhooks-whatsapp/app', WhatsappWebhookAPIView.as_view(), name='whatsapp-webhook'),
    path('whatsapp-app/send-message', WhatsappSendAPIView.as_view()),

    # whatsapp api
    path('whatsapp/by-setting/<int:id>', WhatsappListAll.as_view(), name='whatsapp-list-all'),
    path('whatsapp/all/<int:id>', WhatsappList.as_view(), name='whatsapp-list'),
    path('whatsapp/agenda/<int:id>', WhatsappAgendaList.as_view()),
    path('whatsapp/store', WhatsappStore.as_view(),       name='whatsapp-store'),
    path('whatsapp/message/<int:id>', WhatsappShow.as_view(),   name='whatsapp-show'),
    path('whatsapp/update-lead/<int:id>',    WhatsappUpdateLead.as_view()),
    path('whatsapp/update-chat/<int:id>', WhatsappUpdate.as_view(),    name='whatsapp-update'),
    path('whatsapp/update-date/<int:id>', WhatsappUpdateDate.as_view(), name='whatsapp-update-date'),
    path('whatsapp/update-openai/<int:id>', WhatsappUpdateOpenai.as_view(), name='whatsapp-update-openai'),
    path('whatsapp/update-generated-response/<int:id>', WhatsappUpdateGeneratedResponse.as_view()),
    path('whatsapp/update-agenda/<int:id>', WhatsappUpdateAgenda.as_view()),
    path('whatsapp/delete/<int:id>',      WhatsappDestroy.as_view(),    name='whatsapp-destroy'),

    # level
    path('level-all', NivelViewSet.as_view({'get': 'listAll'}), name='level-all'),
    path('level', nivel_list, name='level-list-create'),
    path('level/<int:pk>', nivel_detail, name='level-detail'),
    path('level/<int:pk>/save-image', nivel_save_image, name='level-save-image'),
    path('level/<int:pk>/estado', NivelViewSet.as_view({ 'put': 'updateState' })),

    # level whatsapp
    path('whatsapp-level/show/<int:id>',   ChatLevelShow.as_view(),   name='chatlevel-show'),
    path('whatsapp-level/update/<int:id>', ChatLevelUpdate.as_view(), name='chatlevel-update'),

    # Nuevas URLs para mensajes en bloque
    path('whatsapp/send-bulk-message', WhatsappBulkSendAPIView.as_view(), name='whatsapp-bulk-send'),

    # APIs para WhatsappMetaPlantillas
    path('whatsapp-meta-plantillas/<int:pk>', WhatsappMetaPlantillasViewSet.as_view({
        'get': 'list'
        }), name='whatsapp-meta-plantillas-list'),
    
    # APIs para WhatsappPlantillaResumen
    path('whatsapp-plantilla-resumen', WhatsappPlantillaResumenViewSet.as_view({
        'get': 'list'
        }), name='whatsapp-plantilla-resumen-list'),

    # APIs para WhatsappConfiguracionUser
    path('whatsapp-configuracion-user/<int:pk>', WhatsappConfiguracionUserViewSet.as_view({
        'get': 'show',
        'put': 'update'
    }), name='whatsapp-configuracion-user-detail'),

     # APIs para WhatsappChatnUser
    path('whatsapp-chat-user/<int:pk>', WhatsapChatUserViewSet.as_view({
        'get': 'show',
        'put': 'update'
    })),

    # API para WhatsappProfileAccepts
    path('whatsapp-profile-accepts/<int:pk>', WhatsappProfileAcceptsViewSet.as_view({
        'get': 'show',
        'put': 'update'
    }), name='whatsapp-profile-accepts-detail'),
    path('whatsapp-profile-accepts-by-name', WhatsappProfileAcceptsViewSet.as_view({'post': 'getProfileAccepts'}), name='whatsapp-profile-accepts-by-name'),

    #lead
    path('whatsapp/lead', LeadViewSet.as_view({
        'post': 'create'
    }), name='whatsapp-lead'),

]
