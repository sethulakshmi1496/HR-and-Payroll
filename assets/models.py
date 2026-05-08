"""
Asset / NOC / Discipline models.

- CompanyAsset: phones, SIMs, laptops, ID-cards, equipment issued to employees.
- NOC: HR-issued template PDFs, employees upload signed copies.
- DisciplineRecord: late-attendance escalations, deductions for payroll.
"""
from django.conf import settings
from django.db import models
from decimal import Decimal


class CompanyAsset(models.Model):
    class AssetType(models.TextChoices):
        PHONE = 'PHONE', 'Phone Handset'
        SIM = 'SIM', 'SIM Card'
        LAPTOP = 'LAPTOP', 'Laptop / Workstation'
        ID_CARD = 'ID_CARD', 'ID Card'
        EQUIPMENT = 'EQUIPMENT', 'Other Equipment'
        OTHER = 'OTHER', 'Other'

    class Status(models.TextChoices):
        ISSUED = 'ISSUED', 'Issued'
        RETURNED = 'RETURNED', 'Returned'
        LOST = 'LOST', 'Lost / Damaged'

    profile = models.ForeignKey(
        'core.EmployeeProfile',
        on_delete=models.PROTECT,
        related_name='assets',
    )
    asset_type = models.CharField(max_length=20, choices=AssetType.choices)
    label = models.CharField(max_length=160, help_text='Model / serial / phone number')
    serial_no = models.CharField(max_length=120, blank=True)
    issued_date = models.DateField()
    returned_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ISSUED)
    notes = models.TextField(blank=True)

    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets_company_asset'
        ordering = ['-issued_date']

    def __str__(self):
        return f"{self.get_asset_type_display()} — {self.label} ({self.profile.employee_id})"


class NOC(models.Model):
    """No-Objection Certificate. HR uploads template, employee returns signed."""
    class Status(models.TextChoices):
        DRAFT = 'DRAFT', 'Draft'
        ISSUED = 'ISSUED', 'Issued'
        SIGNED = 'SIGNED', 'Signed Returned'
        CLOSED = 'CLOSED', 'Closed'

    profile = models.ForeignKey(
        'core.EmployeeProfile',
        on_delete=models.PROTECT,
        related_name='nocs',
    )
    purpose = models.CharField(max_length=200, default='General')
    template_pdf = models.FileField(upload_to='nocs/templates/%Y/', blank=True, null=True)
    signed_pdf = models.FileField(upload_to='nocs/signed/%Y/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+',
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'assets_noc'
        ordering = ['-created_at']


class DisciplineRecord(models.Model):
    """
    Late-attendance escalation log. Created automatically by the
    attendance signal at 2nd / 3rd / 4th+ late events in a month.
    Payroll service reads this to deduct salary days.

    Severity rule:
      - 2nd late event  -> WARN (email only, no deduction)
      - 3rd late event  -> DEDUCT_HALF_DAY (0.5d)
      - 4th+ late event -> DEDUCT_FULL_DAY (1.0d each)
    Cinema departments are exempt (record never created).
    """
    class Severity(models.TextChoices):
        WARN = 'WARN', 'Warning (email)'
        DEDUCT_HALF_DAY = 'HALF', '0.5 day cut'
        DEDUCT_FULL_DAY = 'FULL', '1.0 day cut'

    class Reason(models.TextChoices):
        LATE_ESCALATION = 'LATE', 'Late attendance escalation'
        ATTENDANCE = 'ATTN', 'Other attendance violation'
        OTHER = 'OTHER', 'Other'

    profile = models.ForeignKey(
        'core.EmployeeProfile',
        on_delete=models.PROTECT,
        related_name='discipline_records',
    )
    attendance = models.ForeignKey(
        'core.Attendance',
        on_delete=models.SET_NULL, null=True, blank=True,
        related_name='discipline_records',
    )
    occurred_on = models.DateField()
    reason = models.CharField(max_length=20, choices=Reason.choices,
                              default=Reason.LATE_ESCALATION)
    severity = models.CharField(max_length=20, choices=Severity.choices)
    deduction_days = models.DecimalField(
        max_digits=4, decimal_places=2, default=Decimal('0'),
        help_text='Days to deduct in payroll for this record',
    )
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True, help_text='HR can revoke')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'assets_discipline'
        ordering = ['-occurred_on']
        indexes = [models.Index(fields=['profile', 'occurred_on'])]
