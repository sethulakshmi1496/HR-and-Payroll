from django.urls import path
from . import views

app_name = 'twofa'

urlpatterns = [
    path('setup/', views.SetupView.as_view(), name='setup'),
    path('verify/', views.VerifyView.as_view(), name='verify'),
    path('disable/', views.DisableView.as_view(), name='disable'),
]
