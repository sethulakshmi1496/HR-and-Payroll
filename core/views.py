from django.shortcuts import render, redirect
from django.contrib.auth import login
from core.models import User, Department, EmployeeProfile

def setup_owner(request):
    if User.objects.exists():
        return redirect('login')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        email = request.POST.get('email')
        first_name = request.POST.get('first_name')
        
        if username and password:
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                first_name=first_name,
                role=User.Role.MD,
                is_superuser=True,
                is_staff=True
            )
            
            # Create HQ Department if it doesn't exist
            dept, _ = Department.objects.get_or_create(
                name='HQ & Operations', 
                defaults={'code': 'HQ', 'is_active': True}
            )
            
            # Create Employee Profile
            EmployeeProfile.objects.create(
                user=user,
                department=dept,
                probation_status=EmployeeProfile.ProbationStatus.PERMANENT
            )
            
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'registration/setup.html')

def signup(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        re_password = request.POST.get('re_password')
        email = request.POST.get('email')
        role = request.POST.get('role')
        
        if password != re_password:
            return render(request, 'registration/signup.html', {'error': 'Passwords do not match.', 'roles': User.Role.choices})
            
        if username and password and email and role:
            if User.objects.filter(username=username).exists():
                return render(request, 'registration/signup.html', {'error': 'Username already taken.', 'roles': User.Role.choices})
                
            user = User.objects.create_user(
                username=username,
                password=password,
                email=email,
                role=role
            )
            
            # Default fallback department to avoid profile crashes
            dept = Department.objects.first()
            if not dept:
                dept = Department.objects.create(name='General', code='GEN', is_active=True)
            
            EmployeeProfile.objects.create(
                user=user,
                department=dept,
                probation_status=EmployeeProfile.ProbationStatus.PROBATION
            )
            
            login(request, user)
            return redirect('dashboard')
            
    return render(request, 'registration/signup.html', {'roles': User.Role.choices})
