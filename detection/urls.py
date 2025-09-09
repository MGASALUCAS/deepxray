from django.urls import path
from . import views

urlpatterns = [
    path('', views.detection_home, name='detection_home'),
    path('login/', views.login_view, name='detection_login'),
    path('register/', views.register_view, name='detection_register'),
    path('logout/', views.logout_view, name='detection_logout'),
    path('upload/', views.upload_xray, name='upload_xray'),
    path('patients/', views.patient_management, name='patient_management'),
    path('results/', views.analysis_results, name='analysis_results'),
]
