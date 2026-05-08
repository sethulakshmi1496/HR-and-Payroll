from django.urls import path
from .views import ClockInOutView, DashboardView

app_name = 'attendance'

urlpatterns = [
    path('clock/', ClockInOutView.as_view(), name='clock'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
