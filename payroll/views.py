"""
Payroll views.

Permissions:
- MD/HR        -> generate, approve, view all, edit incentives (MD-only).
- Dept Head    -> view (read-only) own dept after generation, 48h review window.
- Staff        -> view & download own payslips only.
"""
from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.mail import send_mail
from django.http import HttpResponse, HttpResponseForbidden, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View

from core.models import (
    AuditLog,
    Department,
    EmployeeProfile,
    Incentive,
    Payroll,
    User,
)
from .pdf import build_payslip_pdf
from .service import (
    KERALA_PT_SLABS,
    PayrollService,
    generate_for_month,
    generate_for_profile,
)


# ────────────────────────── Mixins ──────────────────────────
class HRorMDRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role in [User.Role.HR, User.Role.MD]


class MDOnlyMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        u = self.request.user
        return u.is_authenticated and u.role == User.Role.MD


# ────────────────────────── Dashboard ──────────────────────────
class PayrollDashboardView(LoginRequiredMixin, View):
    """Main payroll page.
    - MD/HR: month selector, list all payrolls, incentives editor (MD only),
             pay history Chart.js.
    - Staff: own pay history + slip download links.
    """
    def get(self, request):
        u = request.user
        today = date.today()
        try:
            year = int(request.GET.get('year', today.year))
            month = int(request.GET.get('month', today.month))
        except (TypeError, ValueError):
            year, month = today.year, today.month

        is_manager = u.role in [User.Role.HR, User.Role.MD]
        is_md = u.role == User.Role.MD

        if is_manager:
            payrolls = Payroll.objects.filter(
                month__year=year, month__month=month
            ).select_related('profile__user', 'profile__department').order_by(
                'profile__department__name', 'profile__employee_id'
            )
            incentives = Incentive.objects.filter(
                month__year=year, month__month=month
            ).select_related('profile__user', 'created_by').order_by('-created_at')
            employees = EmployeeProfile.objects.filter(is_active=True).select_related('user', 'department')
            history_qs = Payroll.objects.filter(status__in=[
                Payroll.Status.HR_APPROVED, Payroll.Status.FINALIZED
            ]).order_by('month')
        else:
            try:
                profile = u.employee_profile
            except EmployeeProfile.DoesNotExist:
                return render(request, 'attendance/error.html',
                              {'message': 'No employee profile linked.'})
            payrolls = Payroll.objects.filter(profile=profile).order_by('-month')[:12]
            incentives = Incentive.objects.filter(profile=profile).order_by('-month')[:12]
            employees = []
            history_qs = payrolls

        # Aggregate Chart.js data: total net by month
        history_map = {}
        for p in history_qs:
            key = p.month.strftime('%Y-%m')
            history_map[key] = history_map.get(key, Decimal('0')) + Decimal(p.net_salary)
        history_labels = sorted(history_map.keys())
        history_values = [float(history_map[k]) for k in history_labels]

        return render(request, 'payroll/dashboard.html', {
            'is_manager': is_manager,
            'is_md': is_md,
            'year': year,
            'month': month,
            'payrolls': payrolls,
            'incentives': incentives,
            'employees': employees,
            'history_labels': history_labels,
            'history_values': history_values,
            'incentive_types': Incentive.IncentiveType.choices,
        })


# ────────────────────────── Generate ──────────────────────────
class GenerateView(HRorMDRequiredMixin, View):
    """POST { year, month, profile_id? } -> generate (or all)."""
    def post(self, request):
        try:
            year = int(request.POST.get('year'))
            month = int(request.POST.get('month'))
        except (TypeError, ValueError):
            messages.error(request, "Invalid year/month")
            return redirect('payroll:dashboard')

        profile_id = request.POST.get('profile_id')
        created = []
        if profile_id:
            profile = get_object_or_404(EmployeeProfile, pk=profile_id)
            created.append(generate_for_profile(profile, year, month))
        else:
            created = generate_for_month(year, month)

        # Email Heads (HEAD_REVIEW notice) — console backend in dev
        heads_emails = list(User.objects.filter(
            role__in=[User.Role.MD, User.Role.DEPT_HEAD],
            is_active=True,
        ).exclude(email='').values_list('email', flat=True))
        if heads_emails:
            send_mail(
                subject=f"[AEC HR] Payroll drafts ready — {month:02d}/{year} (48h review)",
                message=(f"{len(created)} payroll drafts have been generated for "
                         f"{month:02d}/{year}. Please review within 48 hours.\n\n"
                         f"Visit /payroll/ to review."),
                from_email='no-reply@aecgroup.in',
                recipient_list=heads_emails,
                fail_silently=True,
            )

        AuditLog.objects.create(
            performed_by=request.user,
            action=AuditLog.ActionType.PAYROLL_GENERATED,
            details={'year': year, 'month': month, 'count': len(created)},
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f"Generated {len(created)} payroll drafts for {month:02d}/{year}.")
        return redirect(f"{reverse_lazy('payroll:dashboard')}?year={year}&month={month}")


# ────────────────────────── Approve ──────────────────────────
class ApproveView(HRorMDRequiredMixin, View):
    """HR/MD approves a single payroll draft."""
    def post(self, request, pk):
        payroll = get_object_or_404(Payroll, pk=pk)
        if payroll.is_locked:
            messages.warning(request, "Payroll already finalized.")
            return redirect(self._dash_url(payroll))

        action = request.POST.get('action', 'approve')
        if action == 'approve':
            payroll.status = Payroll.Status.HR_APPROVED
            payroll.reviewed_by = request.user
        elif action == 'finalize':
            payroll.status = Payroll.Status.FINALIZED
            payroll.is_locked = True
            payroll.finalized_at = timezone.now()
            payroll.reviewed_by = request.user
        payroll.save()

        AuditLog.objects.create(
            profile=payroll.profile,
            performed_by=request.user,
            action=(AuditLog.ActionType.PAYROLL_FINALIZED
                    if action == 'finalize' else AuditLog.ActionType.PAYROLL_GENERATED),
            details={'status': payroll.status, 'pk': payroll.pk},
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f"Payroll {action}d.")
        return redirect(self._dash_url(payroll))

    def _dash_url(self, payroll):
        return (f"{reverse_lazy('payroll:dashboard')}"
                f"?year={payroll.month.year}&month={payroll.month.month}")


# ────────────────────────── Slip (PDF) ──────────────────────────
class SlipView(LoginRequiredMixin, View):
    def get(self, request, year, month):
        u = request.user
        # Determine which profile's slip
        profile_id = request.GET.get('profile_id')
        if profile_id and u.role in [User.Role.HR, User.Role.MD]:
            profile = get_object_or_404(EmployeeProfile, pk=profile_id)
        else:
            try:
                profile = u.employee_profile
            except EmployeeProfile.DoesNotExist:
                raise Http404("No employee profile.")

        payroll = Payroll.objects.filter(
            profile=profile, month__year=year, month__month=month
        ).first()
        if not payroll:
            raise Http404("Payslip not generated for this month.")
        if (u.role == User.Role.STAFF
                and payroll.status not in [Payroll.Status.HR_APPROVED, Payroll.Status.FINALIZED]):
            return HttpResponseForbidden("Payslip not yet approved.")

        pdf_data = build_payslip_pdf(payroll)
        resp = HttpResponse(pdf_data, content_type='application/pdf')
        fname = f"payslip_{profile.employee_id}_{year}_{month:02d}.pdf"
        resp['Content-Disposition'] = f'attachment; filename="{fname}"'
        return resp


# ────────────────────────── Tax page ──────────────────────────
class TaxPageView(HRorMDRequiredMixin, View):
    """Tracks municipal/building/stationery payments — read-only list with
    sample seed entries (replace with model later)."""
    def get(self, request):
        # Summary cards from existing payrolls
        latest_payrolls = Payroll.objects.order_by('-month')[:50]
        total_pt = sum((Decimal(p.pt_deduction) for p in latest_payrolls), Decimal('0'))
        total_esi = sum((Decimal(p.esi_deduction) for p in latest_payrolls), Decimal('0'))
        total_pf = sum((Decimal(p.pf_deduction) for p in latest_payrolls), Decimal('0'))

        return render(request, 'payroll/tax.html', {
            'kerala_pt_slabs': KERALA_PT_SLABS,
            'total_pt': total_pt,
            'total_esi': total_esi,
            'total_pf': total_pf,
        })


# ────────────────────────── Incentive CRUD (MD only) ──────────────────────────
class IncentiveAddView(MDOnlyMixin, View):
    def post(self, request):
        try:
            profile = get_object_or_404(EmployeeProfile, pk=request.POST.get('profile_id'))
            incentive_type = request.POST.get('incentive_type')
            amount = Decimal(request.POST.get('amount') or '0')
            description = request.POST.get('description', '')
            visuals_pct = Decimal(request.POST.get('visuals_pct') or '0')
            year = int(request.POST.get('year'))
            month = int(request.POST.get('month'))
        except Exception as e:
            messages.error(request, f"Invalid input: {e}")
            return redirect('payroll:dashboard')

        Incentive.objects.create(
            profile=profile,
            incentive_type=incentive_type,
            amount=amount,
            description=description,
            visuals_pct=visuals_pct,
            month=date(year, month, 1),
            created_by=request.user,
        )
        AuditLog.objects.create(
            profile=profile, performed_by=request.user,
            action=AuditLog.ActionType.INCENTIVE_ADDED,
            details={'amount': str(amount), 'type': incentive_type},
            ip_address=request.META.get('REMOTE_ADDR'),
        )
        messages.success(request, f"Incentive added for {profile.employee_id}.")
        return redirect(f"{reverse_lazy('payroll:dashboard')}?year={year}&month={month}")


class IncentiveDeleteView(MDOnlyMixin, View):
    def post(self, request, pk):
        inc = get_object_or_404(Incentive, pk=pk)
        year, month = inc.month.year, inc.month.month
        inc.delete()
        messages.success(request, "Incentive removed.")
        return redirect(f"{reverse_lazy('payroll:dashboard')}?year={year}&month={month}")
