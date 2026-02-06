# users/views/theme_views.py
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required

from users.models import SubjectMember
from users.services.customer_profile_service import ProfileService


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
    addresses = subject.addresses.all()

    return render(
        request,
        "storefront/address.html",
        {
            "theme_base": theme_base,
            "addresses": addresses,
        }
    )
