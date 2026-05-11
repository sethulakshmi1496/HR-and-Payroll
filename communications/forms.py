from django import forms
from core.models import EmployeeProfile

class PromotionForm(forms.Form):
    employee = forms.ModelChoiceField(
        queryset=EmployeeProfile.objects.filter(is_active=True),
        widget=forms.Select(attrs={'class': 'w-full p-2 border rounded mt-1'})
    )
    new_designation = forms.CharField(max_length=100, widget=forms.TextInput(attrs={'class': 'w-full p-2 border rounded mt-1', 'placeholder': 'e.g. Senior Manager'}))
    new_salary = forms.DecimalField(max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'class': 'w-full p-2 border rounded mt-1'}))
    effective_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full p-2 border rounded mt-1'}))
