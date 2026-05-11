from django import forms
from .models import InviteToken
from core.models import Department

class HRInviteForm(forms.ModelForm):
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        empty_label="Select Department",
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded mt-1'})
    )
    
    class Meta:
        model = InviteToken
        fields = ['email', 'department']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'w-full p-2 border rounded mt-1', 'placeholder': 'candidate@example.com'})
        }

from core.models import EmployeeProfile
class OfferLetterForm(forms.ModelForm):
    duties = forms.CharField(widget=forms.Textarea(attrs={'class': 'w-full p-2 border rounded mt-1', 'rows': 4}))
    probation_duration = forms.CharField(required=False, label="Probation Duration", widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded mt-1', 'placeholder': 'e.g. 3 Months, 6 Months'}))
    additional_notes = forms.CharField(required=False, label="Additional HR Messages", widget=forms.Textarea(attrs={'class': 'w-full p-2 border rounded mt-1', 'rows': 3, 'placeholder': 'e.g. You will be made permanent based on your performance.'}))
    class Meta:
        model = EmployeeProfile
        fields = ['designation', 'probation_status', 'basic_salary', 'date_of_joining']
        widgets = {
            'designation': forms.TextInput(attrs={'class': 'w-full p-2 border rounded mt-1', 'placeholder': 'Job Position'}),
            'probation_status': forms.Select(attrs={'class': 'w-full p-2 border rounded mt-1'}),
            'basic_salary': forms.NumberInput(attrs={'class': 'w-full p-2 border rounded mt-1'}),
            'date_of_joining': forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded mt-1'}),
        }

class CandidateOnboardingForm(forms.Form):
    first_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}))
    last_name = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}))
    phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}))
    personal_account = forms.CharField(max_length=30, label="Bank Account Number (Probation)", widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}))
    aadhaar = forms.CharField(max_length=12, label="Aadhaar Number", widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded'}))
    
    # Files
    profile_pic = forms.ImageField(required=True, widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}))
    academic_doc = forms.FileField(required=True, label="Highest Academic Certificate", widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}))
    id_proof = forms.FileField(required=True, label="ID Proof (Aadhaar/PAN)", widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}))
    exp_letter = forms.FileField(required=False, label="Experience Letter (if any)", widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}))
    salary_slips = forms.FileField(required=False, label="Previous Salary Slips (if any)", widget=forms.FileInput(attrs={'class': 'w-full p-2 border rounded'}))
