from django.contrib import admin
from .models import CompanyAsset, NOC, DisciplineRecord


@admin.register(CompanyAsset)
class CompanyAssetAdmin(admin.ModelAdmin):
    list_display = ('asset_type', 'label', 'profile', 'status', 'issued_date')
    list_filter = ('asset_type', 'status')
    search_fields = ('label', 'serial_no', 'profile__employee_id')


@admin.register(NOC)
class NOCAdmin(admin.ModelAdmin):
    list_display = ('profile', 'purpose', 'status', 'created_at')
    list_filter = ('status',)


@admin.register(DisciplineRecord)
class DisciplineRecordAdmin(admin.ModelAdmin):
    list_display = ('profile', 'severity', 'occurred_on', 'deduction_days', 'is_active')
    list_filter = ('severity', 'reason', 'is_active')
    search_fields = ('profile__employee_id',)
