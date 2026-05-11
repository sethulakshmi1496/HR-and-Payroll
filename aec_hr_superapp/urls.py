"""
URL configuration for aec_hr_superapp project.
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect, render
from django.contrib.auth import views as auth_views
from core.views import setup_owner, signup

@login_required
def dashboard(request):
    ctx = {}
    if request.user.role == 'MD':
        from core.models import EmployeeProfile, Attendance, LeaveRequest
        from django.utils import timezone
        today = timezone.now().date()
        ctx['md_stats'] = {
            'total_employees':    EmployeeProfile.objects.filter(is_active=True).count(),
            'on_probation':       EmployeeProfile.objects.filter(is_active=True, probation_status='PROBATION').count(),
            'permanent_employees':EmployeeProfile.objects.filter(is_active=True, probation_status='PERMANENT').count(),
            'present_today':      Attendance.objects.filter(date=today, is_valid=True).count(),
            'on_leave_today':     LeaveRequest.objects.filter(
                                      status='APPROVED',
                                      start_date__lte=today,
                                      end_date__gte=today
                                  ).count(),
        }
    return render(request, 'dashboard.html', ctx)

urlpatterns = [
    # Redirect base URL to dashboard, login, or setup
    path('', lambda r: redirect('dashboard') if r.user.is_authenticated else (redirect('setup') if not __import__('core').models.User.objects.exists() else redirect('login'))),
    path('setup/', setup_owner, name='setup'),
    
    path('admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('accounts/signup/', signup, name='signup'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('i18n/', include('django.conf.urls.i18n')),
    path('dashboard/', dashboard, name='dashboard'),
    
    # AEC Super App Modules
    path('onboarding/', include('onboarding.urls')),
    path('attendance/', include('attendance.urls')),
    path('payroll/', include('payroll.urls')),
    path('leave/', include('leave.urls')),
    path('assets/', include('assets.urls')),
    path('communications/', include('communications.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)