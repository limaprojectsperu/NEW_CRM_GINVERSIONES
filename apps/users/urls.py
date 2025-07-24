from django.urls import path, re_path
from .views.users import UsersViewSet 
from .views.user_tokens import UserTokensViewSet 
from .views.permissions import PermissionsViewSet 
from .views.perfiles import PerfilesViewSet 
from .views.perfil_permissions import PerfilPermissionsViewSet 
from .views.wasabi import WasabiFileHandler, WasabiFileUpload
from .views.access import AccesosViewSet

urlpatterns = [
     # URLs para Users
    path('users', UsersViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='users-list'),
    path('users/<int:pk>', UsersViewSet.as_view({
        'put': 'update',
        #'delete': 'destroy'
    }), name='users-detail'),
    
    # URLs para UserTokens
    path('user-tokens', UserTokensViewSet.as_view({
        #'get': 'list',
        'post': 'create'
    }), name='user-tokens-list'),
    path('user-tokens/<int:pk>', UserTokensViewSet.as_view({
        #'put': 'update',
        'delete': 'destroy'
    }), name='user-tokens-detail'),
    
    # URLs para Permissions
    #path('permissions', PermissionsViewSet.as_view({
        #'get': 'list',
        #'post': 'create'
    #}), name='permissions-list'),
   # path('permissions/<int:pk>', PermissionsViewSet.as_view({
        #'put': 'update',
        #'delete': 'destroy'
    #}), name='permissions-detail'),
    
    # URLs para Perfiles
    path('perfiles', PerfilesViewSet.as_view({
        'get': 'list',
        'post': 'create'
    }), name='perfiles-list'),
    path('perfiles/<int:pk>', PerfilesViewSet.as_view({
        'put': 'update',
        #'delete': 'destroy'
    }), name='perfiles-detail'),
    
    # URLs para PerfilPermissions
    #path('perfil-permissions', PerfilPermissionsViewSet.as_view({
        #'get': 'list',
        #'post': 'create'
    #}), name='perfil-permissions-list'),
    #path('perfil-permissions/<int:pk>', PerfilPermissionsViewSet.as_view({
        #'put': 'update',
        #'delete': 'destroy'
    #}), name='perfil-permissions-detail'),

    # Obtener accesos por perfil
    path('access/perfil/<int:perfil_id>/', AccesosViewSet.as_view({
        'get': 'get_access_perfil'
    }), name='access-perfil'),
    # Obtener estructura jerárquica de accesos
    path('access/tree/', AccesosViewSet.as_view({
        'get': 'get_access_tree'
    }), name='access-tree'),
    # Guardar accesos para un perfil
    path('access/perfil/<int:perfil_id>/store/', AccesosViewSet.as_view({
        'post': 'store_access_perfil'
    }), name='access-store'),
    # Mostrar accesos de un perfil
    path('access/perfil/<int:perfil_id>/show/', AccesosViewSet.as_view({
        'get': 'show_access_perfil'
    }), name='access-show'),

    # Ruta específica para URLs pre-firmadas (redirección), imagenes
    re_path(
        r'^img/(?P<path>[^/]+)/?(?P<path2>[^/]+)?/?(?P<path3>[^/]+)?/?(?P<path4>[^/]+)?/?(?P<file>[^/]+)?/?$',
        WasabiFileHandler.as_view(),
        {'action': 'redirect'},
        name='wasabi_image'
    ),
    # Para PDFs específicamente
    re_path(
        r'^file/(?P<path>[^/]+)/?(?P<path2>[^/]+)?/?(?P<path3>[^/]+)?/?(?P<path4>[^/]+)?/?(?P<file>[^/]+)?/?$',
        WasabiFileHandler.as_view(),
        name='wasabi_file'
    ),
    # Ruta para subir archivos
    path('files/upload', WasabiFileUpload.as_view(), name='wasabi_upload'),

]
