"""Register daily background schedules: birthday SMS, anniversary SMS,
and yearly Kerala holiday fetch."""
from django.db import migrations
from django.utils import timezone


def create_schedules(apps, schema_editor):
    try:
        from django_q.models import Schedule
    except Exception:
        return

    now = timezone.now()
    daily_run = now.replace(hour=8, minute=0, second=0, microsecond=0)
    if daily_run < now:
        daily_run = daily_run + timezone.timedelta(days=1)

    Schedule.objects.update_or_create(
        name='birthday-sms-daily',
        defaults={
            'func': 'leave.tasks.birthday_sms',
            'schedule_type': Schedule.DAILY,
            'next_run': daily_run,
            'repeats': -1,
        },
    )
    Schedule.objects.update_or_create(
        name='anniversary-sms-daily',
        defaults={
            'func': 'leave.tasks.anniversary_sms',
            'schedule_type': Schedule.DAILY,
            'next_run': daily_run,
            'repeats': -1,
        },
    )
    Schedule.objects.update_or_create(
        name='kerala-holiday-fetch-yearly',
        defaults={
            'func': 'leave.tasks.holiday_fetch_kerala',
            'schedule_type': Schedule.YEARLY,
            'next_run': daily_run.replace(month=1, day=1),
            'repeats': -1,
        },
    )

    # Run the holiday fetch once now so depts have data.
    try:
        from leave.tasks import holiday_fetch_kerala
        holiday_fetch_kerala(timezone.now().year)
    except Exception:
        pass


def remove_schedules(apps, schema_editor):
    try:
        from django_q.models import Schedule
    except Exception:
        return
    Schedule.objects.filter(name__in=[
        'birthday-sms-daily',
        'anniversary-sms-daily',
        'kerala-holiday-fetch-yearly',
    ]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('django_q', '0019_alter_task_options_alter_ormq_key_alter_ormq_lock_and_more'),
        ('core', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(create_schedules, remove_schedules),
    ]
