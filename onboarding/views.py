import os
from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.urls import reverse
from django.utils import timezone
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from core.models import User, EmployeeProfile, AuditLog
from .models import InviteToken
from .forms import HRInviteForm, CandidateOnboardingForm
from .utils import generate_official_joining_letter

class HRRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role in [User.Role.HR, User.Role.MD]

class InviteView(HRRequiredMixin, View):
    def get(self, request):
        form = HRInviteForm()
        return render(request, 'onboarding/invite.html', {'form': form})

    def post(self, request):
        form = HRInviteForm(request.POST)
        if form.is_valid():
            invite = form.save()
            invite_url = request.build_absolute_uri(reverse('onboarding:candidate', args=[invite.id]))
            
            # Send Email
            subject = f"Join AEC Group - {invite.department.name}"
            body = f"Hello,\n\nYou have been invited to join AEC Group ({invite.department.name}).\n\nPlease complete your onboarding by clicking the link below:\n{invite_url}\n\nThis link expires in 7 days."
            email = EmailMessage(subject, body, to=[invite.email])
            email.send()
            
            return redirect('onboarding:invite')
        return render(request, 'onboarding/invite.html', {'form': form})

class CandidateView(View):
    def get(self, request, token):
        invite = get_object_or_404(InviteToken, id=token)
        if not invite.is_valid:
            return render(request, 'onboarding/invalid_token.html')
        form = CandidateOnboardingForm()
        return render(request, 'onboarding/candidate_form.html', {'form': form, 'invite': invite})

    def post(self, request, token):
        invite = get_object_or_404(InviteToken, id=token)
        if not invite.is_valid:
            return render(request, 'onboarding/invalid_token.html')
            
        form = CandidateOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            # Create Inactive User
            username = form.cleaned_data['email'] if 'email' in form.cleaned_data else invite.email
            user = User.objects.create_user(
                username=username,
                email=invite.email,
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                phone=form.cleaned_data['phone'],
                profile_picture=request.FILES['profile_pic'],
                is_active=False # Pending HR Verification
            )
            
            # Handle File Uploads for Docs Vault
            fs = FileSystemStorage(location=os.path.join(settings.MEDIA_ROOT, 'docs_vault'))
            docs_vault = {}
            for doc_field in ['academic_doc', 'id_proof', 'exp_letter', 'salary_slips']:
                file = request.FILES.get(doc_field)
                if file:
                    filename = fs.save(f"{invite.id}_{file.name}", file)
                    docs_vault[doc_field] = {
                        'url': fs.url(filename),
                        'verified': False,
                        'uploaded_at': timezone.now().isoformat()
                    }
                    
            # Mask Aadhaar
            aadhaar_raw = form.cleaned_data['aadhaar']
            aadhaar_masked = f"XXXXXXXX{aadhaar_raw[-4:]}" if len(aadhaar_raw) >= 4 else "INVALID"

            # Create Draft Profile
            profile = EmployeeProfile.objects.create(
                user=user,
                department=invite.department,
                personal_account=form.cleaned_data['personal_account'],
                aadhaar_masked=aadhaar_masked,
                docs_vault=docs_vault,
                probation_status=EmployeeProfile.ProbationStatus.PROBATION,
                notice_period_days=30,
                is_locked=False
            )
            
            invite.is_used = True
            invite.profile = profile
            invite.save()
            
            return render(request, 'onboarding/success.html')
            
        return render(request, 'onboarding/candidate_form.html', {'form': form, 'invite': invite})

class HRVerifyView(HRRequiredMixin, View):
    def get(self, request):
        pending_profiles = EmployeeProfile.objects.filter(is_locked=False, user__is_active=False)
        return render(request, 'onboarding/hr_verify.html', {'profiles': pending_profiles})

    def post(self, request):
        profile_id = request.POST.get('profile_id')
        action = request.POST.get('action')
        profile = get_object_or_404(EmployeeProfile, id=profile_id)
        
        if action == 'confirm':
            profile.is_locked = True
            profile.user.is_active = True
            profile.date_of_joining = timezone.now().date()
            profile.save()
            profile.user.save()
            
            # Generate PDF and Email
            pdf_data, pdf_path = generate_official_joining_letter(profile)
            
            subject = f"Welcome to AEC Group - Official Joining Letter"
            body = f"Dear {profile.user.first_name},\n\nYour documents have been verified. Welcome to AEC Group!\n\nPlease find your official joining letter attached."
            email = EmailMessage(subject, body, to=[profile.user.email])
            email.attach(f"Joining_Letter_{profile.employee_id}.pdf", pdf_data, 'application/pdf')
            email.send()
            
            # Audit Log
            AuditLog.objects.create(
                profile=profile,
                performed_by=request.user,
                action=AuditLog.ActionType.PROFILE_LOCKED,
                details={'notes': 'HR Verified Docs, Sent PDF'},
                ip_address=request.META.get('REMOTE_ADDR')
            )
            
        elif action == 'reject':
            # Quick-remove (Delete Draft)
            user = profile.user
            profile.delete()
            user.delete()
            
        return redirect('onboarding:hr_verify')
