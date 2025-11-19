from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.utils import timezone
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from .models import LoginSession, TwoFactorCode
from django.conf import settings
from .signals import get_client_ip

# Create your views here.

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            ##Code for generating and sending 6-digits 2FA code ##
            code = TwoFactorCode.generate_code()
            TwoFactorCode.objects.create(user=user, code=code)
            send_mail(
                'Your 2FA code',
                f'Your one-time login code is: {code}',
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            ##login(request, user) -- for normal login without 2FA
            request.session['pending_user'] = user.id
            request.session.modified = True
            request.session.save()

            print("Debug: pending_user set -> ", request.session['pending_user'])

            # Redirect to 2FA verification page
            return redirect('verify_2fa')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'accounts/login.html')

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        email = request.POST['email']
        user = User.objects.create_user(username=username, password=password, email=email)
        messages.success(request, 'Account created successfully.')
        return redirect('/login/')
    return render(request, 'accounts/signup.html')

def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST['email']
        form = PasswordResetForm({'email': email})
        if form.is_valid():
            form.save(
                request=request,
                use_https=False,
                email_template_name='accounts/password_reset_email.html',
            )
            messages.success(request, 'Password reset email sent.')
            return redirect('/login/')
    return render(request, 'accounts/forgot_password.html')

@login_required
def session_logs_view(request):
    sessions = LoginSession.objects.filter(user=request.user).order_by('-login_time')
    return render(request, 'accounts/session_logs.html', {'sessions': sessions})

def verify_2fa_view(request):
    if 'pending_user' not in request.session:
        return redirect('login')
    
    user_id = request.session['pending_user']
    user = get_object_or_404(User, id=user_id)

    if request.method =='POST':
        code = request.POST['code']
        valid = TwoFactorCode.objects.filter(user=user, code=code, is_used=False).last()
        if valid and valid.is_valid():
            valid.is_used = True
            valid.save()
            login(request, user)
            LoginSession.objects.create(
                user=user, 
                ip_address=get_client_ip(request), 
                user_agent=request.META.get('HTTP_USER_AGENT', 'unknown')
            )
            del request.session['pending_user']
            return redirect('/admin/') ##or tenant dashboard
        else:
            messages.error(request, 'Invalid or expired code.')
    return render(request, 'accounts/verify_2fa.html')

@login_required
def logout_view(request):
    current_key = request.session.session_key
    if current_key:
        LoginSession.objects.filter(
            user=request.user,
            session_key=current_key, 
            is_active=True
        ).update(is_active=False, logout_time=timezone.now())
    logout(request)
    return redirect('/login/')

@login_required
def logout_all_devices_view(request):
    LoginSession.objects.filter(user=request.user, is_active=True).update(
        is_active=False, logout_time=timezone.now()
    )
    logout(request)
    return redirect('/login/')

#this is a test comment deleted in next commit