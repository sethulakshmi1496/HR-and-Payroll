import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "aec_hr_superapp.settings")
django.setup()

from django.test import Client
from core.models import User

c = Client()
u = User.objects.get(username='hr_aec')
c.force_login(u)

try:
    response = c.get('/attendance/clock/')
    if response.status_code != 200:
        print(f"Status Code: {response.status_code}")
        if response.context and 'exception' in response.context:
            print(response.context['exception'])
    else:
        print("Works fine")
except Exception as e:
    import traceback
    traceback.print_exc()
