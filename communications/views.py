from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import PromotionForm
from twofa.emails import send_html_mail
from core.models import User
import datetime

def is_hr_or_md(user):
    return user.is_authenticated and user.role in [User.Role.HR, User.Role.MD]

@login_required
@user_passes_test(is_hr_or_md)
def send_promotion(request):
    if request.method == 'POST':
        form = PromotionForm(request.POST)
        if form.is_valid():
            profile = form.cleaned_data['employee']
            new_designation = form.cleaned_data['new_designation']
            new_salary = form.cleaned_data['new_salary']
            effective_date = form.cleaned_data['effective_date']
            
            # Send Email
            try:
                send_html_mail(
                    subject="AEC Group - Official Promotion Letter",
                    template_name="communications/email_promotion.html",
                    context={
                        'profile': profile,
                        'new_designation': new_designation,
                        'new_salary': new_salary,
                        'effective_date': effective_date,
                    },
                    to=[profile.user.email]
                )
                
                # Update Profile
                profile.designation = new_designation
                profile.basic_salary = new_salary
                
                docs_vault = profile.docs_vault or {}
                docs_vault['promotion_letter'] = {
                    'url': f"System Generated Email on {datetime.date.today()}",
                    'verified': True,
                    'details': f"Promoted to {new_designation} with ₹{new_salary}"
                }
                profile.docs_vault = docs_vault
                profile.save()
                
                messages.success(request, f"Promotion letter sent to {profile.user.get_full_name()}. Profile updated & securely logged in Vault.")
                return redirect('communications:send_promotion')
            except Exception as e:
                messages.error(request, f"Failed to send promotion email. Please check SMTP.")
    else:
        form = PromotionForm()
        
    return render(request, 'communications/send_promotion.html', {'form': form})
