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

        # 1. Validity: GPS geofence for mobile / IP whitelist for desktop
        is_valid = True
        if lat and lon:
            # GPS available → use 100 m geofence if dept coords are configured
            if dept.latitude and dept.longitude:
                dist = haversine_distance(lat, lon, dept.latitude, dept.longitude)
                if dist > 100:
                    is_valid = False
            # If dept has no geofence coords configured, GPS is present but we trust it
        else:
            # No GPS (desktop / laptop) → check IP whitelist
            if dept.allowed_ips:
                client_ip = request.META.get('REMOTE_ADDR', '')
                allowed = [ip.strip() for ip in dept.allowed_ips.split(',') if ip.strip()]
                is_valid = client_ip in allowed
            else:
                # No IP restriction configured → allow all desk logins
                is_valid = True

        # 2. Save Face Image
        face_image_path = ""
        if face_b64:
            try:
                format, imgstr = face_b64.split(';base64,') 
                ext = format.split('/')[-1]
                filename = f"{profile.employee_id}_{timezone.now().strftime('%Y%m%d%H%M%S')}.{ext}"
                file_path = os.path.join(settings.MEDIA_ROOT, 'attendance_faces', filename)
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "wb") as fh:
                    fh.write(base64.b64decode(imgstr))
                face_image_path = os.path.join('media', 'attendance_faces', filename)
            except Exception:
                pass

        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        is_mobile = 'mobi' in user_agent or 'android' in user_agent or 'iphone' in user_agent

        # 3. Create or Update Attendance
        today = timezone.now().date()
        attendance, created = Attendance.objects.get_or_create(
            profile=profile,
            date=today,
            defaults={
                'source': Attendance.ClockSource.MOBILE if is_mobile else Attendance.ClockSource.DESKTOP,
                'ip_address': request.META.get('REMOTE_ADDR')
            }
        )
        
        attendance.gps_latitude = lat
        attendance.gps_longitude = lon
        attendance.face_image_path = face_image_path
        attendance.is_valid = is_valid
        attendance.location_name = dept.name  # store office/department as location label
        
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
            # MD/HR View: All attendance for today with Heatmap data
            from core.models import Department
            today = timezone.now().date()
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


class LivePresenceView(LoginRequiredMixin, View):
    """JSON endpoint polled every 30s by the dashboard to refresh
    the heatmap / map without a page reload."""
    def get(self, request):
        from core.models import Department

        if request.user.role not in [User.Role.MD, User.Role.HR, User.Role.DEPT_HEAD]:
            return JsonResponse({'error': 'forbidden'}, status=403)

        today = timezone.now().date()
        todays = Attendance.objects.filter(date=today, in_time__isnull=False).select_related(
            'profile__user', 'profile__department'
        )
        if request.user.role == User.Role.DEPT_HEAD:
            todays = todays.filter(profile__department__head=request.user)

        depts = Department.objects.filter(is_active=True).order_by('name')
        labels, presents, totals = [], [], []
        for d in depts:
            total_emp = d.employees.filter(is_active=True).count()
            if total_emp == 0:
                continue
            labels.append(d.code)
            presents.append(todays.filter(profile__department=d, is_valid=True).count())
            totals.append(total_emp)

        markers = [
            {
                'name': r.profile.user.get_full_name(),
                'dept': r.profile.department.code,
                'lat': float(r.gps_latitude) if r.gps_latitude else None,
                'lon': float(r.gps_longitude) if r.gps_longitude else None,
                'in': r.in_time.isoformat() if r.in_time else None,
                'out': r.out_time.isoformat() if r.out_time else None,
                'is_late': r.is_late,
            }
            for r in todays if r.gps_latitude and r.gps_longitude
        ]

        return JsonResponse({
            'as_of': timezone.now().isoformat(),
            'labels': labels,
            'present': presents,
            'total': totals,
            'markers': markers,
        })