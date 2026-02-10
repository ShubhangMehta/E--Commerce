from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.db import transaction

from accounts.services import get_or_create_global_user
from users.models import SubjectMember, TenantRole
from themes.views import _theme_path
import logging
logger = logging.getLogger(__name__)

@transaction.atomic
def tenant_customer_signup(request):
    if request.method == "POST":
        logger.warning("🔥 tenant_customer_signup CALLED | host=%s | schema=%s | method=%s",
                   request.get_host(),
                   getattr(getattr(request, "tenant", None), "schema_name", "unknown"),
                   request.method)
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "").strip()
        full_name = request.POST.get("full_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        if not email or not password or not full_name:
            messages.error(request, "Please fill in all required fields.")
            return redirect("tenant_customer_signup")

        # Create or get global user
        user, created = get_or_create_global_user(email, password)

        # Create SubjectMember in tenant schema
        SubjectMember.objects.get_or_create(
            global_user_id=user.id,
            defaults={
                "role": TenantRole.CUSTOMER,
                "full_name": full_name,
                "email": email,
                "phone": phone,
                "is_active": True,
            }
        )

        # Authenticate and log in the user
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
        return redirect("index")

    return render(request, _theme_path("signup.html"))

