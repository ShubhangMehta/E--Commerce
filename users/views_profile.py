from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.http import urlencode
from django.utils import timezone
from django.contrib.auth import authenticate, login
from django.db import connection
from django.conf import settings
from django.db import transaction
from django_tenants.utils import schema_context
from users.permissions import require_roles
from customers.views import ensure_owner_global_identity_is_new

from themes.views import _theme_path
from .models import SubjectMember, Coordinate, TenantRole, StaffInvite
from core_app.emails.utils import send_html_email
from accounts.services import get_or_create_global_user
from django.db.models import Q
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context, get_public_schema_name

@login_required
def users_home(request):
        if connection.schema_name == "public": #temp fix 
            return redirect("/")  # or raise 404
        users = SubjectMember.objects.all()

        User = get_user_model()
        search_query = request.GET.get("q", "").strip()

        # 🔍 Search by full_name only
        if search_query:
            users = users.filter(
                full_name__icontains=search_query
            )

        # Get all global_user_ids from tenant users
        global_ids = [u.global_user_id for u in users]

        # Fetch last_login from public schema
        with schema_context(get_public_schema_name()):
            global_users = User.objects.filter(id__in=global_ids).values("id", "last_login")

        # Convert to dictionary {id: last_login}
        last_login_map = {u["id"]: u["last_login"] for u in global_users}

        # Attach last_login to each SubjectMember instance
        for user in users:
            user.last_login = last_login_map.get(user.global_user_id)

        # Tenant + theme
        client = request.tenant
        theme = client.theme

        return render(request, "dashboard.html", {
            "users": users,
            "tenant": client,
            "theme_base": f"themes/{theme}/storefront.html",
        })


INVITE_RULES = {
    TenantRole.OWNER: {TenantRole.ADMIN, TenantRole.STAFF},
    TenantRole.ADMIN: {TenantRole.STAFF},
    TenantRole.STAFF: set(),
    TenantRole.CUSTOMER: set(),
}

def allowed_invite_roles(inviter_role: str):
    return INVITE_RULES.get(inviter_role, set())


@login_required
@require_roles(TenantRole.ADMIN, TenantRole.OWNER)
def staff_invite_view(request):
    inviter_role = request.subject_member.role
    allowed = allowed_invite_roles(inviter_role)

    invite_roles = [(r, dict(TenantRole.choices)[r]) for r in allowed]

    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        role = request.POST.get("role", TenantRole.STAFF).strip()

        if role not in allowed:
            messages.error(request, "You don't have permission to invite this role.")
            return render(request, "staff/invite_create.html", {"invite_roles": invite_roles, "old": {"email": email},})
        
    if request.method == "POST":
        email = request.POST.get("email", "").strip().lower()
        role = request.POST.get("role", TenantRole.STAFF).strip()

        inv = StaffInvite.objects.create(
            email=email,
            role=role,
            invited_by_global_user_id=request.user.id,
        )

        #Force login first; after login user returns to accept link
        accept_path = f"/staff/accept/{inv.token}/"
        login_url = f"/login/?{urlencode({'next': accept_path})}"
        accept_path = f"https://{request.get_host()}{login_url}"

        send_html_email(
            subject="You're invited to join as staff",
            to_email=email,
            template_name="emails/staff_invite.html",
            context={
                "tenant_name": request.tenant.tenant_name,
                "role": role,
                "accept_url": accept_path,
                "expires_at": inv.expires_at,   
            })
        
        return redirect("staff_list")
    
    return render(request, "staff/invite_create.html", {"roles": TenantRole.choices})

@login_required
def staff_invite_accept(request, token):
    inv = get_object_or_404(StaffInvite, token=token)

    if not inv.is_valid():
        return render(request, "staff/invite_invalid.html", {"reason": "Invite is expired or invalid."})
    
    #ensure the logged in global user matches invited email
    if ((request.user.email or "").strip().lower() != inv.email.strip().lower()):
        return render(request, "staff/invite_invalid.html", {"reason": f"This invite is for {inv.email}. You are logged in as {request.user.email}."})
    
    member, created = SubjectMember.objects.get_or_create(
        global_user_id=request.user.id,
        defaults={
            "role": inv.role,
            "full_name": request.user.get_full_name() or request.user.get_username(),
            "email": request.user.email,
            "phone": None,
            "is_active": True,
        }
    )

    #Upgarde role is needed
    if not created and member.role != inv.role:
        member.role = inv.role
        member.is_active = True
        member.save(update_fields=["role", "is_active"])

    inv.accepted_at = timezone.now()
    inv.save(update_fields=["accepted_at"])

    return redirect("dashboard")

@login_required
@require_roles(TenantRole.OWNER, TenantRole.ADMIN)
def staff_list(request):
    staff = SubjectMember.objects.filter(is_active=True).exclude(role=TenantRole.CUSTOMER)
    invites = StaffInvite.objects.filter(accepted_at__isnull=True, revoked_at__isnull=True)

    # Role Matrix compute (ADD THIS HERE)
    inviter_role = request.subject_member.role
    allowed = allowed_invite_roles(inviter_role)
    can_invite = len(allowed) > 0

    return render(request, "staff/list.html", {"staff": staff, "invites": invites, "can_invite": can_invite})

@login_required
@require_roles(TenantRole.OWNER, TenantRole.ADMIN)
def staff_invite_revoke(request, token):
    inv = get_object_or_404(StaffInvite, token=token)
    inv.revoked_at = timezone.now()
    inv.save(update_fields=["revoked_at"])
    return redirect("staff_list")

@login_required
@require_roles(TenantRole.OWNER, TenantRole.ADMIN)
def staff_deactivate(request, member_id):
    m = get_object_or_404(SubjectMember, id=member_id)
    if m.role == TenantRole.OWNER:
        # never disable owner from UI
        return redirect("staff_list")
    m.is_active = False
    m.save(update_fields=["is_active"])
    return redirect("staff_list")
    

@transaction.atomic
def tenant_customer_signup(request):

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
        return redirect("users:profile")

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
        return redirect("users:profile")
    
    if request.method == "POST":
        addr = Coordinate.objects.create(
            user=member,
            address_line1=request.POST.get("address_line1", "").strip(),
            address_line2=request.POST.get("address_line2", "").strip(),
            landmark=request.POST.get("landmark", "").strip(),
            city=request.POST.get("city", "").strip(),
            state=request.POST.get("state", "").strip(),
            postal_code=request.POST.get("postal_code", "").strip(),
            country=request.POST.get("country", "").strip(),
            address_type=request.POST.get("address_type", "home"),
            is_default=(request.POST.get("is_default") == "on"),
        )

        if addr.is_default:
            Coordinate.objects.filter(user=member).exclude(id=addr.id).update(is_default=False)

        messages.success(request, "Address added.")
        return redirect("users:profile")
    

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
        addr.address_line1 = request.POST.get("address_line1", "").strip()
        addr.address_line2 = request.POST.get("address_line2", "").strip()
        addr.landmark = request.POST.get("landmark", "").strip()
        addr.city = request.POST.get("city", "").strip()
        addr.state = request.POST.get("state", "").strip()
        addr.postal_code = request.POST.get("postal_code", "").strip()
        addr.address_type = request.POST.get("address_type", "home")
        addr.country = request.POST.get("country", "").strip()
        addr.is_default = (request.POST.get("is_default") == "on")
        addr.save()

        if addr.is_default:
            Coordinate.objects.filter(user=member).exclude(id=addr.id).update(is_default=False)

        messages.success(request, "Address updated.")
        return redirect("users:profile")

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
        return redirect("users:profile")

    return render(request, _theme_path(request,"address_delete_confirm.html"), {
        "storefront": _theme_path(request, "storefront.html"),
        "address": addr,
    })
