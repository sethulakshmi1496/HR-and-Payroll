"""
Attendance signals.
- post_save Attendance: if employee clocked-in late (>15 min after shift start
  in *local* time), flag is_late + late_minutes. Cinema departments are
  exempt from late tracking.
- Wrapped in django-q2 async_task in production; runs synchronously in dev
  (Q_CLUSTER['sync']=True).
"""
from datetime import timedelta

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from core.models import Attendance


SHIFT_START_HOUR = 9   # 09:00 local time (Asia/Kolkata)
SHIFT_START_MIN = 0


def _process_late_check(attendance_id: int) -> None:
    """Worker function: re-fetch & flag late if applicable."""
    try:
        att = Attendance.objects.select_related('profile__department').get(pk=attendance_id)
    except Attendance.DoesNotExist:
        return

    if not att.in_time:
        return
    if att.profile.department.is_cinema:
        return  # Cinema exempt from late penalty

    # Convert in_time to local timezone
    local_in = timezone.localtime(att.in_time)
    shift_start_local = local_in.replace(
        hour=SHIFT_START_HOUR, minute=SHIFT_START_MIN, second=0, microsecond=0,
    )
    grace = timedelta(minutes=getattr(settings, 'GRACE_PERIOD_MINUTES', 15))

    if local_in > (shift_start_local + grace):
        late_min = int((local_in - shift_start_local).total_seconds() / 60)
        Attendance.objects.filter(pk=att.pk).update(
            is_late=True, late_minutes=late_min,
        )


@receiver(post_save, sender=Attendance)
def check_late_attendance(sender, instance, created, **kwargs):
    """
    Trigger late-flag check when an Attendance row is created or updated
    with an in_time. We dispatch via django-q2 async_task; with
    Q_CLUSTER['sync']=True in dev, this runs immediately.
    """
    # Only check when an in_time is present
    if instance.in_time is None:
        return
    # Avoid re-recursion when our own update sets is_late
    if kwargs.get('update_fields') and 'is_late' in (kwargs.get('update_fields') or set()):
        return

    try:
        from django_q.tasks import async_task
        async_task('attendance.signals._process_late_check', instance.pk)
    except Exception:
        # Fallback: synchronous
        _process_late_check(instance.pk)
