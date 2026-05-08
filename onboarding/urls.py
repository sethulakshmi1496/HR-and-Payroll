from django.urls import path
<<<<<<< HEAD
from .views import InviteView, CandidateView, HRVerifyView
=======
from .views import InviteView, CandidateView, HRVerifyView, ProfileUnlockView
>>>>>>> origin/conflict_080526_1642

app_name = 'onboarding'

urlpatterns = [
    path('invite/', InviteView.as_view(), name='invite'),
    path('hr/verify/', HRVerifyView.as_view(), name='hr_verify'),
<<<<<<< HEAD
=======
    path('hr/unlock/<int:pk>/', ProfileUnlockView.as_view(), name='unlock'),
>>>>>>> origin/conflict_080526_1642
    path('<uuid:token>/', CandidateView.as_view(), name='candidate'),
]
