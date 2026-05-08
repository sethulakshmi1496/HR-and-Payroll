from django.urls import path
from . import views

app_name = 'leave'

urlpatterns = [
    path('', views.LeaveListView.as_view(), name='list'),
    path('new/', views.LeaveCreateView.as_view(), name='create'),
    path('<int:pk>/decision/', views.LeaveDecisionView.as_view(), name='decision'),
    path('<int:pk>/cancel/', views.LeaveCancelView.as_view(), name='cancel'),
]
