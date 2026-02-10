from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.db import connection
from django.db import transaction
from django_tenants.utils import schema_context
from customers.views import ensure_owner_global_identity_is_new

from themes.views import _theme_path
from .models import SubjectMember, Coordinate, TenantRole
from accounts.services import get_or_create_global_user

import logging
logger = logging.getLogger(__name__)

@transaction.atomic
def tenant_customer_signup(request):
    logger.warning(
        "🔥 tenant_customer_signup CALLED | host=%s | schema=%s | method=%s",
        request.get_host(),
        getattr(getattr(request, "tenant", None), "schema_name", "unknown"),
        request.method
    )

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()  # only if you add this input in HTML
        email = request.POST.get("email", "").strip().lower()
        username = request.POST.get("username", "").strip().lower()  # using email as username
        password = request.POST.get("password", "").strip()
        confirm_password = request.POST.get("confirm_password", "").strip()

        if not email or not username or not password or not first_name:
            messages.error(request, "Please fill in all required fields.")
            return render(request, _theme_path(request, "signup.html"))

        if password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, _theme_path(request, "signup.html"))
        
        ok, errors = ensure_owner_global_identity_is_new(
        request,
        email=email, 
        username=username,
        )
    
        if not ok:
            return render(request, _theme_path(request, "signup.html"), {"data": request.POST, "errors": errors})
        
        # Create/get GLOBAL user (usually in public schema in django-tenants setups)
        with schema_context("public"):
            user, created = get_or_create_global_user(first_name, last_name, username, email, password)

        # Create the tenant member in TENANT schema
        SubjectMember.objects.get_or_create(
            global_user_id=user.id,
            defaults={
                "role": TenantRole.CUSTOMER,
                "full_name": f"{first_name} {last_name}".strip(),
                "email": email,
                "phone": phone,
                "is_active": True,
            }
        )

        # Log the user in
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)

        return redirect("index")  # or "store_index" etc.

    # ✅ GET must render signup page
    return render(request, _theme_path(request, "signup.html"))

@login_required
def profile_view(request):
    member = SubjectMember.objects.filter(global_user_id=request.user.id).first()
    
    if member is None:
        member = SubjectMember.objects.create(
            global_user_id=request.user.id,
            role=TenantRole.CUSTOMER,
            full_name=request.user.get_username(),
            email=(getattr(request.user, "email", "") or request.user.get_username()),
            phone=None,
            is_active=True,
        )
    
    if request.method == "POST":
        member.full_name = request.POST.get("full_name", "").strip()
        member.phone = request.POST.get("phone", "").strip()
        member.role = request.POST.get("role", member.role).strip()
        member.save()
        messages.success(request, "Profile updated.")
        return redirect("profile")

    addresses = Coordinate.objects.filter(user=member).order_by("-is_default", "-id")

    return render(request, _theme_path(request, "profile.html"), {
        "storefront": _theme_path(request, "storefront.html"),
        "member": member,
        "addresses": addresses,
    })


@login_required
def address_add(request):
    member = request.subject_member
    if member is None:
        return redirect("profile")
    
    if request.method == "POST":
        addr = Coordinate.objects.create(
            user=member,
            full_name=request.POST.get("full_name", "").strip() or member.full_name,
            phone=request.POST.get("phone", "").strip() or (member.phone or ""),
            house_no=request.POST.get("house_no", "").strip(),
            landmark=request.POST.get("landmark", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            postal_code=request.POST.get("postal_code", "").strip(),
            address_type=request.POST.get("address_type", "home"),
            is_default=(request.POST.get("is_default") == "on"),
        )

        if addr.is_default:
            Coordinate.objects.filter(user=member).exclude(id=addr.id).update(is_default=False)

        messages.success(request, "Address added.")
        return redirect("profile")
    

    return render(request, _theme_path(request, "address_form.html"), {
        "storefront": _theme_path(request, "storefront.html"),
        "member": member,
        "address": None,
    })


@login_required
def address_edit(request, address_id: int):
    member = request.subject_member
    addr = get_object_or_404(Coordinate, id=address_id, user=member)

    if request.method == "POST":
        addr.full_name = request.POST.get("full_name", "").strip()
        addr.phone = request.POST.get("phone", "").strip()
        addr.house_no = request.POST.get("house_no", "").strip()
        addr.landmark = request.POST.get("landmark", "").strip()
        addr.city = request.POST.get("city", "").strip()
        addr.state = request.POST.get("state", "").strip()
        addr.postal_code = request.POST.get("postal_code", "").strip()
        addr.address_type = request.POST.get("address_type", "home")
        addr.is_default = (request.POST.get("is_default") == "on")
        addr.save()

        if addr.is_default:
            Coordinate.objects.filter(user=member).exclude(id=addr.id).update(is_default=False)

        messages.success(request, "Address updated.")
        return redirect("profile")

    return render(request, _theme_path(request, "address_form.html"), {
        "storefront": _theme_path(request, "storefront.html"),
        "member": member,
        "address": addr,
    })


@login_required
def address_delete(request, address_id: int):
    member = request.subject_member
    addr = get_object_or_404(Coordinate, id=address_id, user=member)

    if request.method == "POST":
        addr.delete()
        messages.success(request, "Address deleted.")
        return redirect("profile")

    return render(request, _theme_path(request,"address_delete_confirm.html"), {
        "storefront": _theme_path(request, "storefront.html"),
        "address": addr,
    })
