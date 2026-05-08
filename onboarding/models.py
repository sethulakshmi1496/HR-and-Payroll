import uuid
from django.db import models
from django.utils import timezone
from datetime import timedelta
from core.models import Department, EmployeeProfile

class InviteToken(models.fields.related.ForeignKey):
    pass # To avoid circular import issues, although not really needed here if we import carefully.

class InviteToken(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    
    # Linked to profile once the candidate completes the form
    profile = models.OneToOneField(
        EmployeeProfile, 
        on_delete=models.SET_NULL, 
        null=True, blank=True,
        related_name='invite_token'
    )

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)
        super().save(*args, **kwargs)

    @property
    def is_valid(self):
        return not self.is_used and self.expires_at > timezone.now()

    def __str__(self):
        return f"{self.email} - {'Used' if self.is_used else 'Pending'}"
