from django.urls import path
from .views.brands import BrandViewSet
from .views.states import EstadoLeadViewSet, SubEstadoLeadViewSet
from .views.chats_template import MessengerPlantillaViewSet

urlpatterns = [
    # messenger api
    path('marcas', BrandViewSet.as_view({ 'get': 'list' })),

    # APIs para EstadoLead
    path('lead-estados-all/<int:red_social>/<int:IDRedSocial>', EstadoLeadViewSet.as_view({ 'get': 'listAll' })),
    path('lead-estado/<int:red_social>/<int:IDRedSocial>', EstadoLeadViewSet.as_view({ 'get': 'list' })),
    path('lead-estado', EstadoLeadViewSet.as_view({
        'post': 'create'
        }), name='estado-lead-list'),
    path('lead-estado/<int:pk>', EstadoLeadViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
        }), name='estado-lead-detail'),
    path('lead-estado/estado/<int:pk>', EstadoLeadViewSet.as_view({ 'put': 'updateState' })),
    
    # APIs para SubEstadoLead
    path('lead-subestados-all/<int:red_social>/<int:IDRedSocial>', SubEstadoLeadViewSet.as_view({ 'get': 'listAll' })),
    path('lead-subestado/<int:red_social>/<int:IDRedSocial>', SubEstadoLeadViewSet.as_view({ 'get': 'list' })),
    path('lead-subestado', SubEstadoLeadViewSet.as_view({
        'post': 'create'
        }), name='subestado-lead-list'),
    path('lead-subestado/<int:pk>', SubEstadoLeadViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
        }), name='subestado-lead-detail'),
    path('lead-subestado/estado/<int:pk>', SubEstadoLeadViewSet.as_view({ 'put': 'updateState' })),

    # APIs Messenger plantilla
    path('messenger-plantillas-all/<int:red_social>', MessengerPlantillaViewSet.as_view({'get': 'listAll'})),
    path('messenger-plantilla/<int:pk>/<int:red_social>', MessengerPlantillaViewSet.as_view({'get': 'list'})),
    path('messenger-plantilla', MessengerPlantillaViewSet.as_view({
        'post': 'create'
    }), name='messenger-plantilla-list'),
    path('messenger-plantilla/<int:pk>', MessengerPlantillaViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='messenger-plantilla-detail'),
    path('messenger-plantilla/estado/<int:pk>', MessengerPlantillaViewSet.as_view({
        'put': 'updateState'
    }), name='messenger-plantilla-update-state'),
    
]
