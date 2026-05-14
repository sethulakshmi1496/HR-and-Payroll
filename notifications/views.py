from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.shortcuts import redirect, render, get_object_or_404
from django.views import View
from django.http import JsonResponse
from django.contrib import messages

from .models import Notification
from core.models import User, LeaveRequest, ReimbursementRequest


class HRorMDMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.role in [User.Role.HR, User.Role.MD]


class NotificationListView(LoginRequiredMixin, View):
    """All users: view all active notifications, mark as read."""
    def get(self, request):
        from django.db.models import Q
        my_profile = getattr(request.user, 'employee_profile', None)
        if not my_profile and hasattr(request.user, 'employeeprofile_set'):
            my_profile = request.user.employeeprofile_set.first()

        base_query = Q(target_profile__isnull=True)
        if my_profile:
            base_query |= Q(target_profile=my_profile)

        notifications = Notification.objects.filter(base_query, is_active=True).select_related('created_by')
        # Annotate read status for current user
        notif_data = []
        for n in notifications:
            notif_data.append({
                'obj': n,
                'is_read': n.read_by.filter(id=request.user.id).exists(),
            })
        
        pending_leaves = []
        pending_reimbursements = []
        if request.user.role == User.Role.HR:
            pending_leaves = LeaveRequest.objects.filter(status='PENDING').select_related('profile__user')
            pending_reimbursements = ReimbursementRequest.objects.filter(status='PENDING').select_related('profile__user')
        elif request.user.role == User.Role.MD:
            pending_leaves = LeaveRequest.objects.filter(status='PENDING', rejection_reason__icontains=f"-> {request.user.username}").select_related('profile__user')
            pending_reimbursements = ReimbursementRequest.objects.filter(status='HR_VERIFIED').select_related('profile__user')

        return render(request, 'notifications/list.html', {
            'notif_data': notif_data,
            'can_post': request.user.role in [User.Role.HR, User.Role.MD],
            'pending_leaves': pending_leaves,
            'pending_reimbursements': pending_reimbursements,
        })



class MarkReadView(LoginRequiredMixin, View):
    """Mark a notification as read for the current user."""
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk, is_active=True)
        notif.read_by.add(request.user)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        return redirect('notifications:list')


class MarkAllReadView(LoginRequiredMixin, View):
    """Mark all notifications as read for the current user."""
    def post(self, request):
        for n in Notification.objects.filter(is_active=True):
            n.read_by.add(request.user)
        return redirect('notifications:list')


class PostNotificationView(HRorMDMixin, View):
    """HR/MD: create a new notification."""
    def post(self, request):
        title = request.POST.get('title', '').strip()
        message = request.POST.get('message', '').strip()
        if not title or not message:
            messages.error(request, 'Title and message are required.')
            return redirect('notifications:list')
        Notification.objects.create(
            title=title,
            message=message,
            created_by=request.user,
        )
        messages.success(request, f'Notification "{title}" posted to all staff.')
        return redirect('notifications:list')


class DeleteNotificationView(HRorMDMixin, View):
    """HR/MD: deactivate (soft-delete) a notification."""
    def post(self, request, pk):
        notif = get_object_or_404(Notification, pk=pk)
        notif.is_active = False
        notif.save()
        messages.success(request, 'Notification removed.')
        return redirect('notifications:list')


class SendStaffWishView(LoginRequiredMixin, View):
    """Staff: send a congratulatory/celebratory wish from announcement board."""
    def post(self, request, notif_id):
        notif = get_object_or_404(Notification, pk=notif_id)
        wish_text = request.POST.get('wish_text', '').strip()
        if not wish_text:
            messages.error(request, "Wish message cannot be empty.")
            return redirect('notifications:list')
            
        if notif.target_profile:
            from communications.models import InternalMail
            InternalMail.objects.create(
                sender=request.user,
                recipient=notif.target_profile.user,
                subject=f"💌 Warm Wishes from {request.user.get_full_name()}",
                body=f"{wish_text}\n\nSent via Announcement Board",
                mail_type='WISH',
            )
            messages.success(request, f"🎉 Your wishes have been sent to {notif.target_profile.user.get_full_name()}!")
        else:
            messages.error(request, "Could not find recipient profile.")
            
        return redirect('notifications:list')
