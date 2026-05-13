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
    u = request.user

    if u.role == 'MD':
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

    from core.models import Department, EmployeeProfile
    departments = Department.objects.filter(is_active=True)
    staff_by_department = []
    for dept in departments:
        profiles = EmployeeProfile.objects.filter(department=dept).select_related('user')
        probation = profiles.filter(probation_status='PROBATION', is_active=True)
        permanent = profiles.filter(probation_status='PERMANENT', is_active=True)
        terminated = profiles.filter(is_active=False).exclude(onboarding_status='VERIFIED')
        staff_by_department.append({
            'department': dept,
            'probation': probation,
            'permanent': permanent,
            'terminated': terminated,
            'total': probation.count() + permanent.count() + terminated.count()
        })
    ctx['staff_by_department'] = staff_by_department

    # --- Reporting manager card (staff view) ---
    from core.models import EmployeeProfile
    from django.db.models import F
    my_profile = EmployeeProfile.objects.filter(
        user__email=u.email
    ).select_related('reporting_manager__user').order_by(
        F('date_of_joining').desc(nulls_last=True),
        F('designation').desc(nulls_last=True),
        '-id'
    ).first()
    
    ctx['my_profile'] = my_profile
    ctx['my_manager'] = my_profile.reporting_manager if my_profile else None

    # --- Team View: employees who report to the logged-in user ---
    try:
        mgr_profile = u.employee_profile
        team = mgr_profile.team_members.filter(is_active=True).select_related('user', 'department')
        ctx['team_members'] = team
    except Exception:
        ctx['team_members'] = []

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