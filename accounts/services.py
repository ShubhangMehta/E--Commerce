from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context, get_public_schema_name
from django.core.mail import send_mail
from django.conf import settings

def get_or_create_global_user(first_name: str, last_name: str, username: str, email: str, password: str):
    """
    Creates/Fetches global identity in public schema.
    Use email as username for simplicity.
    """
    email = email.strip().lower()
    with schema_context(get_public_schema_name()):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": first_name, "last_name": last_name},
        )
        if created:
            user.set_password(password)
            user.save()
        return user, created
    
# def send_ticket_status_update_email(ticket):
#     """Send email to client when ticket status is updated"""
    
#     status_display = ticket.get_status_display()
    
#     subject = f"Update on Your Support Ticket #{ticket.id} - {ticket.subject}"

#     message = f"""
# Dear {ticket.user.get_full_name() or ticket.user.email},

# Your support ticket has been updated by our team.

# **Ticket ID:** #{ticket.id}
# **Subject:** {ticket.subject}
# **Current Status:** {status_display}

# {ticket.admin_response if ticket.admin_response else ''}

# Thank you for your patience.
# If you have any further questions, feel free to reply to this email.

# Best regards,
# E-Cartel Support Team
#     """

#     try:
#         send_mail(
#             subject=subject,
#             message=message.strip(),
#             from_email=settings.DEFAULT_FROM_EMAIL,
#             recipient_list=[ticket.user.email],
#             fail_silently=False,
#         )
#         print(f"✅ Email sent successfully for ticket #{ticket.id}")
#     except Exception as e:
#         print(f"❌ Failed to send email for ticket #{ticket.id}: {e}")