"""
Context processor: injects unread_notification_count into every template.
"""
from notifications.models import Notification
from core.models import LeaveRequest, ReimbursementRequest, User


def notification_count(request):
    if not request.user.is_authenticated:
        return {}
    try:
        from django.db.models import Q
        my_profile = getattr(request.user, 'employee_profile', None)
        if not my_profile and hasattr(request.user, 'employeeprofile_set'):
            my_profile = request.user.employeeprofile_set.first()

        base_query = Q(target_profile__isnull=True)
        if my_profile:
            base_query |= Q(target_profile=my_profile)

        count = Notification.objects.filter(
            base_query,
            is_active=True
        ).exclude(
            read_by=request.user
        ).count()

        if request.user.role == User.Role.HR:
            count += LeaveRequest.objects.filter(status='PENDING').count()
            count += ReimbursementRequest.objects.filter(status='PENDING').count()
        elif request.user.role == User.Role.MD:
            count += LeaveRequest.objects.filter(status='PENDING', rejection_reason__icontains=f"-> {request.user.username}").count()
            count += ReimbursementRequest.objects.filter(status='HR_VERIFIED').count()
    except Exception:
        count = 0
    return {'unread_notification_count': count}
