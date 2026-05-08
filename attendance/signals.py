from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from datetime import timedelta
from core.models import Attendance

@receiver(post_save, sender=Attendance)
def check_late_attendance(sender, instance, created, **kwargs):
    """
    Stub for Celery task. Checks if the employee is late.
    Triggered post-save of Attendance.
    """
    if created and instance.in_time and not instance.profile.department.is_cinema:
        # Assuming standard shift start is 09:00 AM local time
        # We simulate a Celery async check here
        shift_start = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
        grace_period = timedelta(minutes=15)
        
        if instance.in_time > (shift_start + grace_period):
            # Calculate late minutes
            late_delta = instance.in_time - shift_start
            
            # Use update() to avoid recursive save() signals
            Attendance.objects.filter(id=instance.id).update(
                is_late=True,
                late_minutes=int(late_delta.total_seconds() / 60)
            )
