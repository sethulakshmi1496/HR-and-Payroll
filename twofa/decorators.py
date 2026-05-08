"""Decorators for role-based access + 2FA enforcement."""
from functools import wraps
from django.shortcuts import redirect
from django.urls import reverse


def md_2fa_required(view_func):
    """Enforce TOTP 2FA for MD users on a per-view basis."""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('login'))
        from core.models import User
        if request.user.role != User.Role.MD:
            return view_func(request, *args, **kwargs)
        if request.session.get('md_2fa_verified'):
            return view_func(request, *args, **kwargs)
        from django_otp.plugins.otp_totp.models import TOTPDevice
        if not TOTPDevice.objects.filter(user=request.user, confirmed=True).exists():
            return redirect(reverse('twofa:setup'))
        return redirect(reverse('twofa:verify'))
    return wrapper
