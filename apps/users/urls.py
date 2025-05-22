from django.urls import path
from .views.brands import BrandViewSet

urlpatterns = [
    # messenger api
    path('marcas', BrandViewSet.as_view({ 'get': 'list' })),

]
