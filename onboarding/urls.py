from django.urls import path
from .views import InviteView, CandidateView, HRVerifyView

app_name = 'onboarding'

urlpatterns = [
    path('invite/', InviteView.as_view(), name='invite'),
    path('hr/verify/', HRVerifyView.as_view(), name='hr_verify'),
    path('<uuid:token>/', CandidateView.as_view(), name='candidate'),
]
