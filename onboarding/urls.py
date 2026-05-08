from django.urls import path
from .views import InviteView, CandidateView, HRVerifyView, ProfileUnlockView

app_name = 'onboarding'

urlpatterns = [
    path('invite/', InviteView.as_view(), name='invite'),
    path('hr/verify/', HRVerifyView.as_view(), name='hr_verify'),
    path('hr/unlock/<int:pk>/', ProfileUnlockView.as_view(), name='unlock'),
    path('<uuid:token>/', CandidateView.as_view(), name='candidate'),
]
