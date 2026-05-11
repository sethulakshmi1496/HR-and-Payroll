from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('promotion/', views.send_promotion, name='send_promotion'),
]
