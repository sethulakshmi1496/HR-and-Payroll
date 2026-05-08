from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('', views.LeaveListView.as_view(), name='list'),
    path('new/', views.LeaveCreateView.as_view(), name='create'),
    path('<int:pk>/decision/', views.LeaveDecisionView.as_view(), name='decision'),
    path('<int:pk>/cancel/', views.LeaveCancelView.as_view(), name='cancel'),
    path('calendar/', views.LeaveCalendarView.as_view(), name='calendar'),
    path('holidays/', views.HolidayListView.as_view(), name='holidays'),
    path('holidays/add/', views.HolidayAddView.as_view(), name='holiday_add'),
    path('holidays/<int:pk>/toggle/', views.HolidayToggleView.as_view(), name='holiday_toggle'),
    path('holidays/<int:pk>/delete/', views.HolidayDeleteView.as_view(), name='holiday_delete'),
    path('holidays/fetch/', views.HolidayFetchView.as_view(), name='holiday_fetch'),
]
