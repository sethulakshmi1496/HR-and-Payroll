import os
import base64
import uuid
from django.shortcuts import render, redirect
from django.views import View
from django.http import JsonResponse
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.files.base import ContentFile

from core.models import Attendance, EmployeeProfile, User
from .utils import haversine_distance

class ClockInOutView(LoginRequiredMixin, View):
    def get(self, request):
        try:
            profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return render(request, 'attendance/error.html', {'message': 'No employee profile linked.'})
            
        today = timezone.now().date()
        attendance = Attendance.objects.filter(profile=profile, date=today).first()
        
        status = 'in' if attendance and attendance.in_time and not attendance.out_time else 'out'
        
        context = {
            'status': status,
            'department': profile.department,
            'attendance': attendance
        }
        return render(request, 'attendance/clock.html', context)

    def post(self, request):
        try:
            profile = request.user.employee_profile
        except EmployeeProfile.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'No profile found'}, status=400)

        data = request.POST
        action = data.get('action') # 'in' or 'out'
        lat = data.get('latitude')
        lon = data.get('longitude')
        face_b64 = data.get('face_image')
        
        dept = profile.department
        
        # 1. Distance Calculation (Geofence 100m)
        is_valid = True
        if lat and lon and dept.latitude and dept.longitude:
            dist = haversine_distance(lat, lon, dept.latitude, dept.longitude)
            if dist > 100:
                is_valid = False
        else:
            # If GPS failed or IP desktop fallback
            is_valid = False 
            
        # 2. Save Face Image
        face_image_path = ""
        if face_b64:
            format, imgstr = face_b64.split(';base64,') 
            ext = format.split('/')[-1]
            filename = f"{profile.employee_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
            file_path = os.path.join(settings.MEDIA_ROOT, 'attendance_faces', filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, "wb") as fh:
                fh.write(base64.b64decode(imgstr))
            face_image_path = os.path.join('media', 'attendance_faces', filename)

        # 3. Create or Update Attendance
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            profile=profile,
            date=today,
            defaults={
                'source': Attendance.ClockSource.MOBILE if lat else Attendance.ClockSource.DESKTOP,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )
        
        attendance.gps_latitude = lat
        attendance.gps_longitude = lon
        attendance.face_image_path = face_image_path
        attendance.is_valid = is_valid
        
        if action == 'in':
            if not attendance.in_time:
                attendance.in_time = timezone.now()
        elif action == 'out':
            attendance.out_time = timezone.now()
            
        attendance.save()
        
        return JsonResponse({
            'success': True, 
            'message': f"Clocked {action} successfully",
            'is_valid': is_valid
        })

class DashboardView(LoginRequiredMixin, View):
    def get(self, request):
        user = request.user
        context = {}
        
        if user.role in [User.Role.MD, User.Role.HR]:
            # MD/HR View: All attendance for today
            from core.models import Department
            from django.utils import timezone as _tz
            today = _tz.now().date()
            todays = Attendance.objects.filter(date=today).select_related(
                'profile__user', 'profile__department'
            )
            context['attendances'] = todays
            context['is_manager'] = True

            # Heatmap aggregation: per department -> present vs total active
            depts = Department.objects.filter(is_active=True).order_by('name')
            labels, presents, totals = [], [], []
            for d in depts:
                total_emp = d.employees.filter(is_active=True).count()
                if total_emp == 0:
                    continue
                present_emp = todays.filter(
                    profile__department=d,
                    in_time__isnull=False,
                    is_valid=True,
                ).count()
                labels.append(d.code)
                presents.append(present_emp)
                totals.append(total_emp)
            context['heatmap_labels'] = labels
            context['heatmap_present'] = presents
            context['heatmap_total'] = totals
        else:
            # Staff View: Personal history
            try:
                profile = user.employee_profile
                context['attendances'] = Attendance.objects.filter(profile=profile).order_by('-date')[:30]
                context['is_manager'] = False
            except EmployeeProfile.DoesNotExist:
                context['attendances'] = []
                context['is_manager'] = False
                
        return render(request, 'attendance/dashboard.html', context)
