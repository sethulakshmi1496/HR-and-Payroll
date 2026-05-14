"""
Notifications — HR posts announcements visible to all app users.
Tracks per-user read status via a ManyToMany.
"""
from django.db import models
from django.conf import settings


class Notification(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posted_notifications',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    # Track which users have read this notification
    read_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='read_notifications',
    )

    NOTIFICATION_TYPES = (
        ('GENERAL', 'General'),
        ('BIRTHDAY_WISH', 'Birthday Wish'),
        ('ANNIVERSARY_WISH', 'Anniversary Wish'),
        ('ONBOARDING_WISH', 'Onboarding Wish'),
        ('PROMOTION_WISH', 'Promotion Wish'),
        ('LATE_WARNING', 'Late Warning'),
    )
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='GENERAL')
    target_profile = models.ForeignKey(
        'core.EmployeeProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='targeted_notifications',
    )

    class Meta:
        db_table = 'notifications_notification'
        ordering = ['-created_at']

    def __str__(self):
        return self.title
