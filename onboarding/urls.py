from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    # HR and Admin Management
    path('', views.onboarding_dashboard, name='index'),
    path('dashboard/', views.onboarding_dashboard, name='onboarding_dashboard'),
    path('invite/', views.invite_candidate, name='invite_candidate'),
    path('offer/create/<int:profile_id>/', views.create_offer, name='create_offer'),
    path('offer/preview/<int:profile_id>/', views.preview_offer, name='preview_offer'),
    path('verify/', views.hr_verify_list, name='hr_verify_list'),
    path('verify/<int:candidate_id>/', views.hr_verify_detail, name='hr_verify_detail'),
    path('unlock/<int:profile_id>/', views.unlock_profile, name='unlock'),
    path('terminate/<int:profile_id>/', views.quick_terminate, name='quick_terminate'),
    path('confirm_permanent/<int:profile_id>/', views.confirm_permanency, name='confirm_permanency'),
    
    # Candidate Facing
    path('form/<uuid:token>/', views.candidate_onboarding_form, name='candidate_form'),
    path('success/', views.onboarding_success, name='onboarding_success'),
]