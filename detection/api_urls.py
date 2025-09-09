from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.api_upload_xray, name='api_upload_xray'),
    path('analyze/', views.api_analyze_xray, name='api_analyze_xray'),
]
