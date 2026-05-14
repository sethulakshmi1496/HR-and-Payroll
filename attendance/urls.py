from django.urls import path
from .views import ClockInOutView, DashboardView, LivePresenceView, ManualAttendanceView

app_name = 'attendance'

urlpatterns = [
    path('clock/', ClockInOutView.as_view(), name='clock'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
    path('manual/', ManualAttendanceView.as_view(), name='manual'),
    path('api/live/', LivePresenceView.as_view(), name='live'),
]