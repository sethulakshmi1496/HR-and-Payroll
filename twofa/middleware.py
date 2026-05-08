"""
EnforceMD2FAMiddleware — for users with role=MD, require TOTP verification
on every login session. Other roles bypass entirely.

Bypass paths (always accessible): static/, media/, login/logout/, the 2FA
setup & verify endpoints, and language-switch URLs.
"""
from django.shortcuts import redirect
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch


class EnforceMD2FAMiddleware:
    EXEMPT_PREFIXES = (
        '/static/', '/media/', '/i18n/',
        '/accounts/login/', '/accounts/logout/',
        '/2fa/', '/admin/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path
        if any(path.startswith(p) for p in self.EXEMPT_PREFIXES):
            return self.get_response(request)
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return self.get_response(request)
        # Lazy-import to avoid app-loading order issues
        from core.models import User
        if user.role != User.Role.MD:
            return self.get_response(request)
        if request.session.get('md_2fa_verified'):
            return self.get_response(request)

        # Check device status
        from django_otp.plugins.otp_totp.models import TOTPDevice
        has_device = TOTPDevice.objects.filter(user=user, confirmed=True).exists()
        try:
            target = reverse('twofa:setup' if not has_device else 'twofa:verify')
        except NoReverseMatch:
            return self.get_response(request)
        if path == target:
            return self.get_response(request)
        return redirect(target)
