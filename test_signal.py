import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aec_hr_superapp.settings")
os.environ.setdefault("DATABASE_URL", "sqlite:///db.sqlite3")  # using sqlite for testing
django.setup()

from core.models import User, Department, EmployeeProfile, Attendance
from django.utils import timezone
from datetime import timedelta

# create user
u, _ = User.objects.get_or_create(username='test_user', email='test@example.com')
# create department
d, _ = Department.objects.get_or_create(name='Test Dept', code='TST')
# create profile
p, _ = EmployeeProfile.objects.get_or_create(user=u, department=d, basic_salary=1000)

# create attendance
now = timezone.now()
in_time = now.replace(hour=10, minute=0, second=0)  # 1 hour late
a, _ = Attendance.objects.get_or_create(profile=p, date=now.date(), defaults={'in_time': in_time})
if a.in_time is None:
    a.in_time = in_time
    a.save()

print("Late minutes:", a.late_minutes)
print("Is late:", a.is_late)
