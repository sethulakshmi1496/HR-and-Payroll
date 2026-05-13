from django import forms
from .models import InviteToken
from core.models import Department, EmployeeProfile

FIELD_CLASS = 'w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-400'

class HRInviteForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        empty_label="Select Department",
        widget=forms.Select(attrs={'class': FIELD_CLASS})
    )
    class Meta:
        model = InviteToken
        fields = ['email', 'department']
        widgets = {
            'email': forms.EmailInput(attrs={'class': FIELD_CLASS, 'placeholder': 'candidate@example.com'})
        }


class OfferLetterForm(forms.ModelForm):
    duties = forms.CharField(widget=forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 4}))
    probation_duration = forms.CharField(required=False, label="Probation Duration",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'e.g. 3 Months, 6 Months'}))
    additional_notes = forms.CharField(required=False, label="Additional HR Messages",
        widget=forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 3}))

    class Meta:
        model = EmployeeProfile
        fields = ['designation', 'probation_status', 'basic_salary', 'date_of_joining']
        widgets = {
            'designation':      forms.TextInput(attrs={'class': FIELD_CLASS}),
            'probation_status': forms.Select(attrs={'class': FIELD_CLASS}),
            'basic_salary':     forms.NumberInput(attrs={'class': FIELD_CLASS}),
            'date_of_joining':  forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}),
        }


class CandidateOnboardingForm(forms.Form):
    # ── Personal ──────────────────────────────────
    first_name  = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': FIELD_CLASS}))
    last_name   = forms.CharField(max_length=50,  widget=forms.TextInput(attrs={'class': FIELD_CLASS}))
    date_of_birth = forms.DateField(required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': FIELD_CLASS}))
    gender      = forms.ChoiceField(required=False,
        choices=[('','— Select —'),('Male','Male'),('Female','Female'),('Other','Other')],
        widget=forms.Select(attrs={'class': FIELD_CLASS}))
    phone       = forms.CharField(max_length=15,  widget=forms.TextInput(attrs={'class': FIELD_CLASS}))
    address     = forms.CharField(required=False,
        widget=forms.Textarea(attrs={'class': FIELD_CLASS, 'rows': 2}))

    # ── Identity ──────────────────────────────────
    aadhaar     = forms.CharField(max_length=12, label="Aadhaar Number",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS, 'placeholder': 'Last 4 digits stored masked'}))
    pan_number  = forms.CharField(max_length=10, required=False, label="PAN Card Number",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS + ' uppercase', 'placeholder': 'ABCDE1234F'}))

    # ── Emergency Contact ─────────────────────────
    emergency_contact_name  = forms.CharField(max_length=100, required=False, label="Emergency Contact Name",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS}))
    emergency_contact_rel   = forms.ChoiceField(required=False, label="Relationship",
        choices=[('','— Select —'),('Spouse','Spouse'),('Parent','Parent'),
                 ('Sibling','Sibling'),('Child','Child'),('Friend','Friend'),('Other','Other')],
        widget=forms.Select(attrs={'class': FIELD_CLASS}))
    emergency_contact_phone = forms.CharField(max_length=15, required=False, label="Emergency Contact Phone",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS}))

    # ── Bank Details ──────────────────────────────
    personal_account = forms.CharField(max_length=30, required=False, label="Bank Account Number",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS + ' font-mono'}))
    salary_account   = forms.CharField(max_length=30, required=False, label="Salary Account Number",
        widget=forms.TextInput(attrs={'class': FIELD_CLASS + ' font-mono'}))

    # ── Documents ─────────────────────────────────
    profile_pic  = forms.ImageField(required=True,
        widget=forms.FileInput(attrs={'class': FIELD_CLASS}))
    academic_doc = forms.FileField(required=True, label="Highest Academic Certificate",
        widget=forms.FileInput(attrs={'class': FIELD_CLASS}))
    id_proof     = forms.FileField(required=True, label="ID Proof (Aadhaar/PAN)",
        widget=forms.FileInput(attrs={'class': FIELD_CLASS}))
    exp_letter   = forms.FileField(required=False, label="Experience Letter (if any)",
        widget=forms.FileInput(attrs={'class': FIELD_CLASS}))
    salary_slips = forms.FileField(required=False, label="Previous Salary Slips (if any)",
        widget=forms.FileInput(attrs={'class': FIELD_CLASS}))
