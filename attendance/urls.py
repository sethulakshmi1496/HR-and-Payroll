from django.urls import path
from .views import ClockInOutView, DashboardView, LivePresenceView

app_name = 'attendance'

urlpatterns = [
    path('clock/', ClockInOutView.as_view(), name='clock'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('api/live/', LivePresenceView.as_view(), name='live'),
]