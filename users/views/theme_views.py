# users/views/theme_views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
from users.models import SubjectMember, Coordinate
from users.services.customer_profile_service import ProfileService
from users.services.customer_address_service import AddressService

def get_active_theme():
    return getattr(settings, "ACTIVE_THEME", "default")


def get_subject_member(request):
    return SubjectMember.objects.get(
        global_user_id=request.user.id,
        is_active=True
    )


@login_required
def customer_profile(request):
    theme = get_active_theme()
    theme_base = f"themes/{theme}/storefront.html"

    subject = get_subject_member(request)
    edit_mode = request.GET.get("edit") == "1"

    if request.method == "POST":
        ProfileService.update_profile(subject, {
            "full_name": request.POST.get("full_name"),
            "phone": request.POST.get("phone"),
        })
        return redirect("users:customer_profile")

    return render(
        request,
        "storefront/profile.html",
        {
            "theme_base": theme_base,
            "subject": subject,
            "edit_mode": edit_mode,
        }
    )


@login_required
def customer_address(request):
    theme = get_active_theme()
    theme_base = f"themes/{theme}/storefront.html"

    subject = get_subject_member(request)

    # 👉 HANDLE FORM ACTIONS
    if request.method == "POST":
        action = request.POST.get("action")

        # ➕ ADD ADDRESS
        if action == "add":
            AddressService.add_address(subject, request.POST)

        # ✏️ EDIT ADDRESS
        elif action == "edit":
            address_id = request.POST.get("address_id")
            address = get_object_or_404(
                Coordinate,
                id=address_id,
                user=subject
            )
            AddressService.update_address(address, request.POST)

        # 🗑️ DELETE ADDRESS
        elif action == "delete":
            address_id = request.POST.get("address_id")
            address = get_object_or_404(
                Coordinate,
                id=address_id,
                user=subject
            )
            AddressService.delete_address(address)

        return redirect("users:customer_address")

    # GET request → show addresses
    addresses = subject.addresses.all().order_by("-is_default")

    return render(
        request,
        "storefront/address.html",
        {
            "theme_base": theme_base,
            "addresses": addresses,
        }
    )

