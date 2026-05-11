from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import InviteToken
from .forms import HRInviteForm, CandidateOnboardingForm
from .utils import send_onboarding_email

from core.models import User

def is_hr_or_md(user):
    return user.is_authenticated and user.role in [User.Role.HR, User.Role.MD]

@login_required
@user_passes_test(is_hr_or_md)
def invite_candidate(request):
    if request.method == 'POST':
        form = HRInviteForm(request.POST)
        if form.is_valid():
            candidate = form.save()
            success = send_onboarding_email(candidate)
            if success:
                messages.success(request, f"Invitation successfully sent to {candidate.email}")
            else:
                messages.error(request, f"Failed to dispatch email. Please check SMTP configuration.")
            return redirect('onboarding:hr_verify_list')
    else:
        form = HRInviteForm()
    return render(request, 'onboarding/invite.html', {'form': form})

@login_required
@user_passes_test(is_hr_or_md)
def hr_verify_list(request):
    from core.models import EmployeeProfile
    
    if request.method == 'POST':
        profile_id = request.POST.get('profile_id')
        action = request.POST.get('action')
        profile = get_object_or_404(EmployeeProfile, id=profile_id)
        
        if action == 'confirm':
            # Instead of activating, redirect to offer creation page
            return redirect('onboarding:create_offer', profile_id=profile.id)
        elif action == 'reject':
            reason_select = request.POST.get('reason_select')
            reason_text = request.POST.get('reason_text')
            reason = reason_text if reason_select == 'Other' else reason_select
            
            profile.onboarding_status = 'REJECTED'
            profile.rejection_reason = reason
            profile.save()
            messages.warning(request, f"Rejected candidate {profile.user.first_name}. Reason: {reason}")
            return redirect('onboarding:hr_verify_list')

    candidates = InviteToken.objects.filter(is_used=False)
    profiles = EmployeeProfile.objects.filter(onboarding_status='PENDING', is_active=False).select_related('user', 'department')
    locked_profiles = EmployeeProfile.objects.filter(is_active=True).select_related('user', 'department')
    
    return render(request, 'onboarding/hr_verify.html', {
        'candidates': candidates,
        'profiles': profiles,
        'locked_profiles': locked_profiles
    })

@login_required
@user_passes_test(is_hr_or_md)
def hr_verify_detail(request, candidate_id):
    candidate = get_object_or_404(InviteToken, id=candidate_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            candidate.status = 'APPROVED'
            candidate.save()
            # Logic to convert candidate to employee profile can go here
            messages.success(request, f"Approved {candidate.full_name}")
        elif action == 'reject':
            candidate.status = 'REJECTED'
            candidate.save()
            messages.warning(request, f"Rejected {candidate.full_name}")
        return redirect('onboarding:hr_verify_list')
    return render(request, 'onboarding/hr_verify_detail.html', {'candidate': candidate})

@login_required
@user_passes_test(is_hr_or_md)
def create_offer(request, profile_id):
    from core.models import EmployeeProfile
    from .forms import OfferLetterForm
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    
    if request.method == 'POST':
        form = OfferLetterForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            request.session[f'offer_duties_{profile.id}'] = form.cleaned_data['duties']
            request.session[f'offer_probation_duration_{profile.id}'] = form.cleaned_data.get('probation_duration', '')
            request.session[f'offer_additional_notes_{profile.id}'] = form.cleaned_data.get('additional_notes', '')
            return redirect('onboarding:preview_offer', profile_id=profile.id)
    else:
        form = OfferLetterForm(instance=profile)
    
    return render(request, 'onboarding/create_offer.html', {'form': form, 'profile': profile})

@login_required
@user_passes_test(is_hr_or_md)
def preview_offer(request, profile_id):
    from core.models import EmployeeProfile
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    duties = request.session.get(f'offer_duties_{profile.id}', '')
    probation_duration = request.session.get(f'offer_probation_duration_{profile.id}', '')
    additional_notes = request.session.get(f'offer_additional_notes_{profile.id}', '')

    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'send':
            import re
            from datetime import timedelta
            
            if profile.probation_status == 'PROBATION' and probation_duration:
                months_match = re.search(r'(\d+)', probation_duration)
                if months_match and profile.date_of_joining:
                    months = int(months_match.group(1))
                    profile.probation_end_date = profile.date_of_joining + timedelta(days=months*30)
                elif profile.date_of_joining:
                    profile.probation_end_date = profile.date_of_joining + timedelta(days=30)
            elif profile.probation_status == 'PROBATION' and profile.date_of_joining:
                profile.probation_end_date = profile.date_of_joining + timedelta(days=30)

            profile.is_active = True
            profile.is_locked = True
            profile.onboarding_status = 'VERIFIED'
            profile.user.is_active = True
            profile.user.save()
            profile.save()
            
            # Send Email
            from twofa.emails import send_html_mail
            try:
                send_html_mail(
                    subject="AEC Group - Official Appointment Letter",
                    template_name="onboarding/email_offer.html",
                    context={'profile': profile, 'duties': duties, 'probation_duration': probation_duration, 'additional_notes': additional_notes},
                    to=[profile.user.email]
                )
                messages.success(request, f"Offer letter successfully sent to {profile.user.get_full_name()} and profile activated.")
            except Exception as e:
                messages.error(request, f"Profile activated, but failed to send email. Check SMTP settings.")
            
            return redirect('onboarding:hr_verify_list')
        elif action == 'edit':
            return redirect('onboarding:create_offer', profile_id=profile.id)
            
    return render(request, 'onboarding/preview_offer.html', {
        'profile': profile, 
        'duties': duties,
        'probation_duration': probation_duration,
        'additional_notes': additional_notes
    })

@login_required
@user_passes_test(is_hr_or_md)
def unlock_profile(request, profile_id):
    from core.models import EmployeeProfile
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'unlock':
            profile.is_locked = False
            messages.success(request, f"Unlocked {profile.user.first_name}'s profile for document re-upload.")
        elif action == 'relock':
            profile.is_locked = True
            messages.success(request, f"Re-locked {profile.user.first_name}'s profile.")
        profile.save()
    return redirect('onboarding:hr_verify_list')

def candidate_onboarding_form(request, token):
    candidate = get_object_or_404(InviteToken, id=token)
    
    # Block resubmission - once used, no editing allowed
    if candidate.is_used:
        return render(request, 'onboarding/already_submitted.html', {'candidate': candidate})
    
    if request.method == 'POST':
        form = CandidateOnboardingForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data
            from core.models import User, EmployeeProfile
            from django.core.files.storage import default_storage
            import uuid
            
            username = candidate.email.split('@')[0]
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create(
                username=username,
                email=candidate.email,
                first_name=data['first_name'],
                last_name=data['last_name'],
                phone=data['phone'],
                profile_picture=data['profile_pic'],
                is_active=False
            )
            user.set_password(str(uuid.uuid4()))
            user.save()

            docs_vault = {}
            for doc_field in ['academic_doc', 'id_proof', 'exp_letter', 'salary_slips']:
                file_obj = data.get(doc_field)
                if file_obj:
                    path = default_storage.save(f"vault/{user.username}/{file_obj.name}", file_obj)
                    docs_vault[doc_field] = {
                        'url': default_storage.url(path),
                        'verified': False
                    }

            profile = EmployeeProfile.objects.create(
                user=user,
                department=candidate.department,
                personal_account=data['personal_account'],
                aadhaar_masked='X'*8 + data['aadhaar'][-4:],
                docs_vault=docs_vault,
                is_locked=True,   # Immediately lock after submission
                is_active=False
            )

            candidate.profile = profile
            candidate.is_used = True
            candidate.save()
            return redirect('onboarding:onboarding_success')
    else:
        form = CandidateOnboardingForm()
    return render(request, 'onboarding/candidate_form.html', {'form': form, 'candidate': candidate})

def onboarding_success(request):
    return render(request, 'onboarding/success.html')

@login_required
@user_passes_test(is_hr_or_md)
def onboarding_dashboard(request):
    from core.models import EmployeeProfile

    verified_candidates = EmployeeProfile.objects.filter(onboarding_status='VERIFIED').select_related('user', 'department')
    rejected_candidates = EmployeeProfile.objects.filter(onboarding_status='REJECTED').select_related('user', 'department')

    # Candidates who submitted the onboarding form and are waiting for HR review
    verification_requests = EmployeeProfile.objects.filter(
        onboarding_status='PENDING',
        is_active=False,
    ).select_related('user', 'department')

    pending_count = verification_requests.count()

    probation_staff = EmployeeProfile.objects.filter(probation_status='PROBATION', is_active=True).select_related('user', 'department')
    permanent_staff = EmployeeProfile.objects.filter(probation_status='PERMANENT', is_active=True).select_related('user', 'department')
    terminated_staff = EmployeeProfile.objects.filter(probation_status='TERMINATED').select_related('user', 'department')

    from datetime import timedelta
    from django.utils import timezone
    today = timezone.now().date()
    seven_days = today + timedelta(days=7)
    
    probation_alerts = EmployeeProfile.objects.filter(
        probation_status='PROBATION',
        is_active=True,
        probation_end_date__lte=seven_days,
        probation_end_date__gte=today
    ).select_related('user', 'department')

    return render(request, 'onboarding/dashboard.html', {
        'verified_candidates': verified_candidates,
        'rejected_candidates': rejected_candidates,
        'verification_requests': verification_requests,
        'pending_count': pending_count,
        'probation_staff': probation_staff,
        'permanent_staff': permanent_staff,
        'terminated_staff': terminated_staff,
        'probation_alerts': probation_alerts,
    })

@login_required
@user_passes_test(is_hr_or_md)
def quick_terminate(request, profile_id):
    from core.models import EmployeeProfile
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        profile.probation_status = 'TERMINATED'
        profile.is_active = False
        profile.user.is_active = False
        profile.user.save()
        profile.save()
        messages.success(request, f"{profile.user.get_full_name()} has been marked as Terminated.")
    return redirect('onboarding:onboarding_dashboard')

@login_required
def confirm_permanency(request, profile_id):
    from core.models import EmployeeProfile
    profile = get_object_or_404(EmployeeProfile, id=profile_id)
    if request.method == 'POST':
        profile.probation_status = 'PERMANENT'
        profile.save()
        messages.success(request, f"{profile.user.get_full_name()} is now a Permanent Employee!")
    return redirect('onboarding:onboarding_dashboard')