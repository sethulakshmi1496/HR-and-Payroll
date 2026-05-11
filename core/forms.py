from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError
from django import forms
from core.models import User

class RoleAuthenticationForm(AuthenticationForm):
    role = forms.ChoiceField(
        choices=User.Role.choices,
        required=True,
        label="Select Role",
        widget=forms.Select(attrs={
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none bg-white'
        })
    )

    def __init__(self, request=None, *args, **kwargs):
        super().__init__(request, *args, **kwargs)
        # Update widgets for username and password to match UI
        self.fields['username'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
        })
        self.fields['password'].widget.attrs.update({
            'class': 'w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none'
        })

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        role = self.cleaned_data.get('role')
        if role and user.role != role:
            raise ValidationError(
                f"Invalid role. This user is not registered as a {dict(User.Role.choices).get(role, role)}.",
                code='invalid_role',
            )
