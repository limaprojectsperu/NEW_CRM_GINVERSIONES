from django.urls import path
from .analyze_chat import ChatAnalyzerView

urlpatterns = [
    #openia Proxy
    path('openai/analyze-chat', ChatAnalyzerView.as_view(), name='analyze_chat'),
]
