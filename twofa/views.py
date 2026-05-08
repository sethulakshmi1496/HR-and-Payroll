"""TOTP 2FA flows for MD users (django-otp + qrcode)."""
from base64 import b64encode
from io import BytesIO

import qrcode
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views import View
from django_otp.plugins.otp_totp.models import TOTPDevice


def _generate_qr_data_uri(otpauth_url: str) -> str:
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = BytesIO()
    img.save(buf, format='PNG')
    return f"data:image/png;base64,{b64encode(buf.getvalue()).decode()}"


class SetupView(LoginRequiredMixin, View):
    """Generate (or reuse unconfirmed) TOTP device + show QR + verify form."""
    template_name = 'twofa/setup.html'

    def get(self, request):
        # Ensure exactly one unconfirmed pending device per user.
        device, _created = TOTPDevice.objects.get_or_create(
            user=request.user, confirmed=False,
            defaults={'name': f'TOTP — {request.user.username}'},
        )
        qr_uri = _generate_qr_data_uri(device.config_url)
        return render(request, self.template_name, {
            'qr_uri': qr_uri,
            'secret': device.bin_key.hex().upper(),
            'config_url': device.config_url,
        })

    def post(self, request):
        token = (request.POST.get('token') or '').strip()
        device = TOTPDevice.objects.filter(user=request.user, confirmed=False).first()
        if not device:
            messages.error(request, _("Setup expired — please retry."))
            return redirect('twofa:setup')
        if device.verify_token(token):
            device.confirmed = True
            device.save()
            request.session['md_2fa_verified'] = True
            messages.success(request, _("Two-factor authentication enabled."))
            return redirect('dashboard')
        messages.error(request, _("Invalid code — try again."))
        return redirect('twofa:setup')


class VerifyView(LoginRequiredMixin, View):
    template_name = 'twofa/verify.html'

    def get(self, request):
        return render(request, self.template_name, {})

    def post(self, request):
        token = (request.POST.get('token') or '').strip()
        for device in TOTPDevice.objects.filter(user=request.user, confirmed=True):
            if device.verify_token(token):
                request.session['md_2fa_verified'] = True
                request.session.modified = True
                next_url = request.POST.get('next') or reverse('dashboard')
                return redirect(next_url)
        messages.error(request, _("Invalid code — try again."))
        return redirect('twofa:verify')


class DisableView(LoginRequiredMixin, View):
    """MD self-service disable (requires re-entering code)."""
    def post(self, request):
        token = (request.POST.get('token') or '').strip()
        verified = False
        for device in TOTPDevice.objects.filter(user=request.user, confirmed=True):
            if device.verify_token(token):
                verified = True
                break
        if not verified:
            messages.error(request, _("Invalid code."))
            return redirect('dashboard')
        TOTPDevice.objects.filter(user=request.user).delete()
        request.session['md_2fa_verified'] = False
        messages.success(request, _("Two-factor authentication disabled."))
        return redirect('dashboard')
