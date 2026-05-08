"""
Data migration: register the monthly payroll auto-generation
Schedule on the 28th of every month at 09:00.

This is idempotent — running it multiple times only ensures the
schedule exists with the right config.
"""
from django.db import migrations
from django.utils import timezone


def create_monthly_schedule(apps, schema_editor):
    try:
        from django_q.models import Schedule
    except Exception:
        return  # django_q not yet migrated; harmless
    name = 'payroll-monthly-28th'
    next_run = timezone.now().replace(day=28, hour=9, minute=0, second=0, microsecond=0)
    if next_run < timezone.now():
        # Move to next month if today > 28 already.
        next_month = next_run.month + 1
        next_year = next_run.year
        if next_month > 12:
            next_month = 1
            next_year += 1
        next_run = next_run.replace(year=next_year, month=next_month)

    Schedule.objects.update_or_create(
        name=name,
        defaults={
            'func': 'payroll.service.scheduled_monthly_generation',
            'schedule_type': Schedule.MONTHLY,
            'next_run': next_run,
            'repeats': -1,
        },
    )


def remove_monthly_schedule(apps, schema_editor):
    try:
        from django_q.models import Schedule
    except Exception:
        return
    Schedule.objects.filter(name='payroll-monthly-28th').delete()


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('django_q', '0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more'),
    ]
    operations = [
        migrations.RunPython(create_monthly_schedule, remove_monthly_schedule),
    ]
