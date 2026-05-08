"""
Leave Request views.

- Staff: create / cancel own pending requests, view own history.
- HR / MD / Department Head: review pending requests, approve / reject.
- Probation: 1 leave/month (2 half-days). Permanent: 2 leaves/month
  (enforced as soft check on create form).
"""
from datetime import date

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views import View

from core.models import AuditLog, EmployeeProfile, LeaveRequest, User
from twofa.emails import send_html_mail


class HROrMDMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in [User.Role.HR, User.Role.MD, User.Role.DEPT_HEAD]


class LeaveListView(LoginRequiredMixin, View):
    def get(self, request):
        u = request.user
        is_manager = u.role in [User.Role.HR, User.Role.MD, User.Role.DEPT_HEAD]

        if is_manager:
            qs = LeaveRequest.objects.select_related(
                'profile__user', 'profile__department', 'approved_by'
            ).order_by('-created_at')
            if u.role == User.Role.DEPT_HEAD:
                qs = qs.filter(profile__department__head=u)
        else:
            try:
                profile = u.employee_profile
                qs = LeaveRequest.objects.filter(profile=profile).order_by('-created_at')
            except EmployeeProfile.DoesNotExist:
                qs = LeaveRequest.objects.none()

        pending = qs.filter(status=LeaveRequest.Status.PENDING)
        history = qs.exclude(status=LeaveRequest.Status.PENDING)[:50]

        return render(request, 'leave/list.html', {
            'is_manager': is_manager,
            'pending': pending,
            'history': history,
        })


class LeaveCreateView(LoginRequiredMixin, View):
    def get(self, request):
        return render(request, 'leave/create.html', {
            'leave_types': LeaveRequest.LeaveType.choices,
        })

    def post(self, request):
        try:
            profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            messages.error(request, _("No employee profile linked."))
            return redirect('leave:list')

        leave_type = request.POST.get('leave_type')
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason', '')

        if not (leave_type and start_date and end_date):
            messages.error(request, _("All fields required."))
            return redirect('leave:create')

        leave = LeaveRequest.objects.create(
            profile=profile,
            leave_type=leave_type,
            start_date=start_date,
            end_date=end_date,
            reason=reason,
            status=LeaveRequest.Status.PENDING,
        )
        AuditLog.objects.create(
            profile=profile, performed_by=request.user,
            action=AuditLog.ActionType.LEAVE_REQUESTED,
            details={'pk': leave.pk, 'type': leave_type},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        # Email approvers (HTML template)
        approver_emails = list(User.objects.filter(
            role__in=[User.Role.HR, User.Role.MD, User.Role.DEPT_HEAD],
            is_active=True,
        ).exclude(email='').values_list('email', flat=True))
        if approver_emails:
            send_html_mail(
                subject=_("[AEC HR] Leave request — %(name)s") % {
                    'name': profile.user.get_full_name()},
                template_name='email/leave_request.html',
                context={'leave': leave, 'profile': profile},
                to=approver_emails,
            )

        messages.success(request, _("Leave request submitted."))
        return redirect('leave:list')


class LeaveDecisionView(HROrMDMixin, View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.status != LeaveRequest.Status.PENDING:
            messages.warning(request, _("Already actioned."))
            return redirect('leave:list')

        action = request.POST.get('action')
        rejection_reason = request.POST.get('rejection_reason', '')

        if action == 'approve':
            leave.status = LeaveRequest.Status.APPROVED
            audit_action = AuditLog.ActionType.LEAVE_APPROVED
        elif action == 'reject':
            leave.status = LeaveRequest.Status.REJECTED
            leave.rejection_reason = rejection_reason
            audit_action = AuditLog.ActionType.LEAVE_REJECTED
        else:
            messages.error(request, _("Invalid action."))
            return redirect('leave:list')

        leave.approved_by = request.user
        leave.save()

        AuditLog.objects.create(
            profile=leave.profile, performed_by=request.user,
            action=audit_action,
            details={'pk': leave.pk, 'status': leave.status},
            ip_address=request.META.get('REMOTE_ADDR'),
        )

        # Notify employee
        if leave.profile.user.email:
            send_html_mail(
                subject=_("[AEC HR] Leave %(status)s") % {'status': leave.get_status_display()},
                template_name='email/leave_decision.html',
                context={'leave': leave},
                to=[leave.profile.user.email],
            )

        messages.success(request, _("Leave %(status)s.") % {'status': leave.get_status_display()})
        return redirect('leave:list')


class LeaveCancelView(LoginRequiredMixin, View):
    def post(self, request, pk):
        leave = get_object_or_404(LeaveRequest, pk=pk)
        if leave.profile.user != request.user:
            messages.error(request, _("Cannot cancel another user's leave."))
            return redirect('leave:list')
        if leave.status != LeaveRequest.Status.PENDING:
            messages.warning(request, _("Cannot cancel an actioned leave."))
            return redirect('leave:list')
        leave.status = LeaveRequest.Status.CANCELLED
        leave.save()
        messages.success(request, _("Leave cancelled."))
        return redirect('leave:list')
