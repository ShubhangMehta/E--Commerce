from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.conf import settings
from .models import LoginSession
from django.utils import timezone

@receiver(user_logged_in, dispatch_uid="accounts_user_logged_in_unique")
def log_user_login(sender, request, user, **kwargs):
    # After login() Django rotates the session; ensure there is a key
    #print("✅ accounts.signals loaded")
    print(user.username, "🟢 Logged in" )
    if not request.session.session_key:
        request.session.save()
    LoginSession.objects.create(
        user=user,
        ip_address=get_client_ip(request),
        user_agent=request.META.get('HTTP_USER_AGENT', 'unknown'),
        session_key=request.session.session_key,
    )

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

@receiver(user_logged_out, dispatch_uid="accounts_user_logged_out_unique")
def log_user_logout(sender, request, user, **kwargs):
    print(user.username, "🔴 logged out")
    # Session_key may be None after logout(), so fall back to latest active session
    qs = LoginSession.objects.filter(user=user, is_active=True)
    if request and request.session and request.session.session_key:
        qs = qs.filter(session_key=request.session.session_key)
    last = qs.order_by('-login_time').first()
    if last:
        last.logout_time = timezone.now()
        last.is_active = False
        last.save()

