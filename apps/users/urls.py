from django.urls import path
from .views.brands import BrandViewSet
from .views.users import UsersViewSet 
from .views.user_tokens import UserTokensViewSet 
from .views.permissions import PermissionsViewSet 
from .views.perfiles import PerfilesViewSet 
from .views.perfil_permissions import PerfilPermissionsViewSet 
from .views.import_data import ImportData

urlpatterns = [
    path('import-data', ImportData.as_view()),

    # messenger api
    path('marcas', BrandViewSet.as_view({ 'get': 'list' })),

     # URLs para Users
    path('users', UsersViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='users-list'),
    path('users/<int:pk>', UsersViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='users-detail'),
    
    # URLs para UserTokens
    path('user-tokens', UserTokensViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='user-tokens-list'),
    path('user-tokens/<int:pk>', UserTokensViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='user-tokens-detail'),
    
    # URLs para Permissions
    path('permissions', PermissionsViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='permissions-list'),
    path('permissions/<int:pk>', PermissionsViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='permissions-detail'),
    
    # URLs para Perfiles
    path('perfiles', PerfilesViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='perfiles-list'),
    path('perfiles/<int:pk>', PerfilesViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='perfiles-detail'),
    
    # URLs para PerfilPermissions
    path('perfil-permissions', PerfilPermissionsViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='perfil-permissions-list'),
    path('perfil-permissions/<int:pk>', PerfilPermissionsViewSet.as_view({
        'put': 'update',
        'delete': 'destroy'
    }), name='perfil-permissions-detail'),
]
