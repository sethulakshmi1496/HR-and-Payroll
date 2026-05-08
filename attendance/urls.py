from django.urls import path
<<<<<<< HEAD
from .views import ClockInOutView, DashboardView
=======
from .views import ClockInOutView, DashboardView, LivePresenceView
>>>>>>> origin/conflict_080526_1642

app_name = 'attendance'

urlpatterns = [
    path('clock/', ClockInOutView.as_view(), name='clock'),
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
<<<<<<< HEAD
=======
    path('api/live/', LivePresenceView.as_view(), name='live'),
>>>>>>> origin/conflict_080526_1642
]
