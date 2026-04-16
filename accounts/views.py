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
from themes.views import _theme_path
from django.contrib.admin.views.decorators import staff_member_required

from customers.models import Ticket
from customers.forms import SupportTicketForm

def login_view(request):
    next_url = request.GET.get('next') or request.POST.get('next') or '/' #Dont give admin page to next url, its will create the endless login loop

    # # Avoid sending users into admin/login loops
    # # (you can tune these rules to match your routing)
    # if next_url.startswith("/admin"):
    #     next_url = "/"

    template = "accounts/login.html" # default for public schema

    if getattr(request, "tenant", None) and request.tenant.schema_name != "public":
        template = _theme_path(request, "login.html")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        # --- Input validation ---
        if not username or not password:
            messages.error(request, "Please enter both username and password.")
            return render(request, template, {"next": next_url})

        user = authenticate(request, username=username, password=password)

        if user is None:
            messages.error(request, "Invalid username or password.")
            return render(request, template, {"next": next_url})

        # ---- Normal user login ----
        if not user.is_staff:
            login(request, user)
            return redirect(next_url)

        # ---- Staff / Superuser → 2FA flow ----
        code = TwoFactorCode.generate_code()
        TwoFactorCode.objects.create(user=user, code=code)

        send_mail(
            "Your 2FA code",
            f"Your one-time login code is: {code}",
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        request.session["pending_user"] = user.id
        request.session["pending_next"] = next_url
        request.session.modified = True

        print("Debug: pending_user set ->", request.session["pending_user"])

        return redirect("verify_2fa")

    # GET request → show login page
    return render(request, template, {"next": next_url})


def signup_view(request):

    # Default template for public site
    template = "accounts/signup.html"

    # Use themed template for tenant sites
    if getattr(request, "tenant", None) and request.tenant.schema_name != "public":
        template = _theme_path(request, "signup.html")

    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        email = request.POST.get("email")

        # ---- Basic validation ----
        if not all([username, password, first_name, last_name, email]):
            messages.error(request, "All fields are required.")
            return render(request, template)

        # Prevent duplicate usernames
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken.")
            return render(request, template)

        # Create user
        User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

        messages.success(request, "Account created successfully.")
        return redirect("/login/")

    # GET request → show signup page
    return render(request, template)


def forgot_password_view(request):

    template = "accounts/forgot_password.html"

    template = "accounts/forgot_password.html" # default for public schema

    if getattr(request, "tenant", None) and request.tenant.schema_name != "public":
        template = _theme_path(request, "password_reset.html")

    if request.method == "POST":
        email = request.POST.get("email")

        if not email:
            messages.error(request, "Please enter your email address.")
            return render(request, template)

        form = PasswordResetForm({"email": email})

        if form.is_valid():
            form.save(
                request=request,
                use_https=False,
                email_template_name="accounts/password_reset_email.html",
            )
            messages.success(request, 'Password reset email sent.')
            return redirect('/login/')
    return render(request, template)

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
            #next_url = request.session.pop('pending_next')
            request.session.pop('pending_user', None)
            return redirect("/admin/")
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


# Client raises ticket
def raise_ticket(request):
    if request.method == 'POST':
        form = SupportTicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.tenant = request.tenant          # Important for multi-tenant
            ticket.user = request.user
            ticket.save()
            messages.success(request, "Your support ticket has been submitted successfully!")
            return redirect('raise_ticket')
    else:
        form = SupportTicketForm()

    return render(request, 'support/raise_ticket.html', {'form': form})


# Super Admin updates status + sends reply
@staff_member_required
def update_ticket(request, ticket_id):
    ticket = get_object_or_404(Ticket, id=ticket_id)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        admin_reply = request.POST.get('admin_response', '')

        ticket.status = new_status
        ticket.admin_response = admin_reply
        if new_status in ['solved', 'closed']:
            ticket.resolved_by = request.user

        ticket.save()

        # Send email reply to client when status becomes Solved
        if new_status == 'solved' and admin_reply:
            send_ticket_reply_email(ticket)

        messages.success(request, f"Ticket #{ticket.id} updated successfully.")
        return redirect('admin_ticket_list')

    return render(request, 'support/admin_update_ticket.html', {'ticket': ticket})


def send_ticket_reply_email(ticket):
    """Send an email update to the user for a support ticket reply."""
    
    recipient_name = ticket.user.get_full_name() or ticket.user.email
    subject = f"Update on your Support Ticket #{ticket.id}: {ticket.subject}"

    message = (
        f"Dear {recipient_name},\n\n"
        f"Your support ticket has been updated.\n\n"
        f"Status: {ticket.get_status_display()}\n"
        f"Our Reply:\n"
        f"{ticket.admin_response}\n\n"
        f"Thank you for contacting E-Cartel support.\n\n"
        f"Best regards,\n"
        f"E-Cartel Support Team"
    )

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[ticket.user.email],
            fail_silently=False,
        )
    except Exception as e:
        # Log error in production instead of print
        print(f"Failed to send email for ticket {ticket.id}: {e}")