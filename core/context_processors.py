"""
Template context processor: build breadcrumbs from the current request.
Returns a list like:
  [{"label": "Payroll", "url": "/payroll/"}, {"label": "Tax"}]
"""
from django.urls import resolve, Resolver404, NoReverseMatch, reverse

# Friendly names per (namespace, url_name) — falls back to title-cased URL name.
NAMESPACE_LABELS = {
    'attendance': 'Attendance',
    'leave': 'Leave',
    'payroll': 'Payroll',
    'onboarding': 'Onboarding',
    'assets': 'Assets & NOC',
    'communications': 'Communications',
}

VIEW_LABELS = {
    'dashboard': 'Dashboard',
    'clock': 'Clock In / Out',
    'list': 'Requests',
    'calendar': 'Calendar',
    'holidays': 'Holidays',
    'create': 'New Request',
    'tax': 'Tax & Statutory',
    'slip': 'Payslip',
    'onboarding_dashboard': 'Dashboard',
    'hr_verify_list': 'Verify Candidates',
    'hr_verify_detail': 'Verify Candidate',
    'invite_candidate': 'Invite Candidate',
    'create_offer': 'Create Offer',
    'preview_offer': 'Offer Preview',
    'send_promotion': 'Promotion Letter',
    'discipline': 'Discipline Records',
}


def _try_reverse(name):
    try:
        return reverse(name)
    except NoReverseMatch:
        return None


def breadcrumbs(request):
    crumbs = []
    path = request.path

    # First crumb: workspace home (Dashboard) when logged in.
    if getattr(request, 'user', None) and request.user.is_authenticated:
        crumbs.append({'label': 'Workspace', 'url': '/dashboard/'})

    try:
        m = resolve(path)
    except Resolver404:
        return {'zh_breadcrumbs': crumbs}

    namespace = m.namespace or ''
    url_name = m.url_name or ''

    if namespace:
        label = NAMESPACE_LABELS.get(namespace, namespace.replace('_', ' ').title())
        # Try to link to the namespace landing page.
        url = _try_reverse(f"{namespace}:dashboard") \
            or _try_reverse(f"{namespace}:list") \
            or _try_reverse(f"{namespace}:onboarding_dashboard") \
            or _try_reverse(f"{namespace}:send_promotion")
        crumbs.append({'label': label, 'url': url})

    if url_name and url_name not in ('dashboard', 'list', 'onboarding_dashboard'):
        leaf = VIEW_LABELS.get(url_name, url_name.replace('_', ' ').title())
        crumbs.append({'label': leaf})

    # If we never added a leaf, mark the last crumb as the current page (drop url).
    if crumbs:
        crumbs[-1] = {'label': crumbs[-1]['label']}

    return {'zh_breadcrumbs': crumbs}


def active_user_profile(request):
    """
    Finds the active EmployeeProfile and corresponding profile picture URL
    for the logged-in user. Explicitly returns None for Managing Director (MD)
    to prevent displaying seeded staff photos.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        if request.user.role == 'MD':
            return {'resolved_profile_picture_url': None}

        # 1. First check if the logged in user has a profile picture directly
        if request.user.profile_picture:
            try:
                return {'resolved_profile_picture_url': request.user.profile_picture.url}
            except ValueError:
                pass
            
        # 2. Check EmployeeProfile linked directly to request.user
        try:
            if hasattr(request.user, 'employeeprofile_set'):
                profile = request.user.employeeprofile_set.first()
                if profile and profile.user.profile_picture:
                    try:
                        return {'resolved_profile_picture_url': profile.user.profile_picture.url}
                    except ValueError:
                        pass
        except Exception:
            pass
            
    return {'resolved_profile_picture_url': None}


def global_wishes_and_alerts(request):
    """
    Ensures daily automated wishes (birthdays, anniversaries) are generated,
    and returns active wish notifications to the template context.
    """
    if getattr(request, 'user', None) and request.user.is_authenticated:
        try:
            from core.wishes_service import ensure_daily_wishes_and_alerts
            ensure_daily_wishes_and_alerts()
            
            from notifications.models import Notification
            wish_notifs = Notification.objects.filter(
                is_active=True,
                notification_type__in=['BIRTHDAY_WISH', 'ANNIVERSARY_WISH', 'ONBOARDING_WISH', 'PROMOTION_WISH']
            ).select_related('target_profile__user', 'target_profile__department').order_by('-created_at')
            
            return {'active_wish_notifications': wish_notifs}
        except Exception:
            pass
    return {'active_wish_notifications': []}
