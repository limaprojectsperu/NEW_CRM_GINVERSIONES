"""
URL configuration for giconfig project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
import os
from django.contrib import admin
from django.urls import path, include
from .views import home_view 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home_view, name='home'), 
    path('admin/', admin.site.urls),
    path('api/', include('apps.users.urls')),
    path('api/', include('apps.redes_sociales.urls')),
    path('api/', include('apps.messenger.urls')),
    path('api/', include('apps.whatsapp.urls')),
    path('api/', include('apps.chat_interno.urls')),
    path('api/', include('apps.openai.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=os.path.join(settings.MEDIA_ROOT, 'media'))
