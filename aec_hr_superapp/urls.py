"""
URL configuration for aec_hr_superapp project.
"""
from django.contrib import admin
from django.contrib.auth.decorators import login_required
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import TemplateView


@login_required
def dashboard(request):
    from django.shortcuts import render
    return render(request, 'dashboard.html')


urlpatterns = [
    path('', lambda r: redirect('dashboard') if r.user.is_authenticated else redirect('login')),
    path('admin/', admin.site.urls),
    path('accounts/', include('django.contrib.auth.urls')),
    path('dashboard/', dashboard, name='dashboard'),
    path('onboarding/', include('onboarding.urls')),
    path('attendance/', include('attendance.urls')),
    path('payroll/', include('payroll.urls')),
]

# Note: MEDIA is served by Django ONLY in DEBUG. Production should keep media
# private behind a proper auth layer (e.g., signed URLs / Nginx X-Accel-Redirect).
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
