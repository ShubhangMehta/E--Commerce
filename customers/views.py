"""
======================================================================
                           CUSTOMERS / BILLING VIEWS
     Clean • Structured • Readable Code with Detailed Descriptions
======================================================================
"""

# --------------------------------------------------------------------
# Imports
# --------------------------------------------------------------------
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils import timezone

import re
import hmac
import hashlib
import uuid
import json
from datetime import timedelta
from dateutil.relativedelta import relativedelta

# --------------------------------------------------------------------
# Models
# --------------------------------------------------------------------
from .models import (
    TenantRequest,
    Ticket,
    SubscriptionPlan,
    RzpPlan,
    RzpSubscription,
    RzpInvoice,
    RzpPayment,
    RzpWebhookEvent,
    Client,
    Domain,
    ClientPayment,
    ClientRefundRequest,
)

#temp
from django.urls import get_resolver

def debug_urls(request):
    urls = []
    for pattern in get_resolver().url_patterns:
        urls.append(str(pattern))
    return HttpResponse("<br>".join(urls))

# --------------------------------------------------------------------
# Razorpay service helpers
# --------------------------------------------------------------------
from .rzp_services import (
    create_subscription as rzp_create_subscription,
    refund_payment as rzp_refund
)


# ====================================================================
#                        STANDARD BILLING VIEWS
# ====================================================================

from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.contrib import messages
from .models import TenantRequest, Domain, SubscriptionPlan


def create_tenant(request):
    # Load Razorpay plans created by admin
    plans = RzpPlan.objects.all().order_by("amount_in_paise")

    return render(request, "create_tenant.html", {"plans": plans})



def home(request):
    return HttpResponse("<h1> Public Index </h1>")


def raise_ticket(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        category = request.POST.get('category')

        if subject and description and category:
            Ticket.objects.create(
                client=request.tenant,
                subject=subject,
                description=description,
                category=category
            )
            messages.success(request, "Your support ticket has been submitted successfully!")
            return redirect('raise_ticket')
        else:
            messages.error(request, "Please fill all fields before submitting.")

    return render(request, 'raise_ticket.html')


def plans(request):
    """Plan listing page."""
    plans = SubscriptionPlan.objects.filter(status='active')
    return render(request, 'customers/plans.html', {'plans': plans})


def refund_request(request):
    # TEMP: you must replace this with actual logged-in tenant
    client = Client.objects.first()  # OR: request.tenant

    if request.method == "POST":
        reason = request.POST.get("reason")
        status = request.POST.get("status", "pending")

        # Choose latest payment for refund
        payment = ClientPayment.objects.filter(client=client).order_by("-created_at").first()

        if not payment:
            return HttpResponse("No payment found for this tenant", status=400)

        ClientRefundRequest.objects.create(
            client=client,
            payment=payment,
            reason=reason,
            status=status,
            refund_type="subscription_cancel",  # default
        )

        return HttpResponse("<h3>Your refund request was submitted successfully!</h3>")

    return render(request, "refund_request.html", {"client": client})

# ====================================================================
#                        RAZORPAY BILLING VIEWS
# ====================================================================

def _next_invoice_number():
    """Generate invoice numbers like INV-ABCDEFGH12"""
    prefix = getattr(settings, "BILLING_INVOICE_PREFIX", "INV")
    return f"{prefix}-{uuid.uuid4().hex[:10].upper()}"


def pricing_page(request):
    """
    Razorpay pricing page.
    """
    plans = RzpPlan.objects.all().order_by("amount_in_paise")

    # Convert paise → rupees
    for p in plans:
        p.amount_in_rupees = p.amount_in_paise / 100

    return render(request, "pricing.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID,
    })


@transaction.atomic
def start_subscription(request):
    """
    Starts Razorpay subscription and creates a local subscription entry.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    # ✅ Correct field extraction
    tenant_name = (request.POST.get("tenant_name") or "").strip().title()
    desired_domain = (request.POST.get("domain") or "").strip().lower()
    email = (request.POST.get("email") or "").strip()
    plan_name = (request.POST.get("plan") or "").strip()
    interval = (request.POST.get("interval") or "").strip()

    brand_color = request.POST.get("brand_color", "#000000")
    theme = request.POST.get("theme", "default")


    # Validate
    if not all([tenant_name, desired_domain, email, plan_name, interval]):
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    # Map domain to schema name
    # Important: tenants cannot have hyphens, spaces, capital letters
    schema_name = desired_domain.replace("-", "").replace(" ", "").lower()

    # Get plan
    try:
        plan = RzpPlan.objects.get(name=plan_name, interval=interval)
    except RzpPlan.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid plan"}, status=400)

    # Create Razorpay subscription on Razorpay server
    try:
        rzp_sub = rzp_create_subscription(plan, customer_notify=True)
    except Exception as e:
        return JsonResponse({"ok": False, "error": f"Razorpay error: {e}"}, status=400)

    # Save subscription locally
    sub = RzpSubscription.objects.create(
        tenant_name=tenant_name,
        desired_domain=desired_domain,
        email=email,
        
        brand_color=brand_color,
        theme=theme,

        plan=plan,
        interval=interval,
        status="created",
        razorpay_subscription_id=rzp_sub["id"],
    )

    # Create initial invoice (pending)
    invoice = RzpInvoice.objects.create(
        subscription=sub,
        invoice_number=_next_invoice_number(),
        amount_in_paise=plan.amount_in_paise,
        currency="INR",
        status="pending",
    )

    # Response to initialize Razorpay checkout modal
    return JsonResponse({
        "ok": True,
        "subscription_id": sub.id,
        "razorpay_subscription_id": sub.razorpay_subscription_id,
        "invoice_number": invoice.invoice_number,
        "amount_in_paise": invoice.amount_in_paise,
        "razorpay_plan_id": plan.razorpay_plan_id,
        "rzp_key": settings.RAZORPAY_KEY_ID,
        "rzp": rzp_sub,  # optional debugging
    })


# ====================================================================
#                        RAZORPAY WEBHOOK HANDLER
# ====================================================================

@csrf_exempt
def razorpay_webhook(request):
    """
    Handles Razorpay subscription & payment events.

    - subscription.activated  → creates TenantRequest (admin will later approve & create Client)
    - payment.captured        → updates invoice & payment
    """

    # ---------- 1. VERIFY SIGNATURE ----------
    body = request.body or b""
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        expected_signature = hmac.new(
            settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            msg=body,
            digestmod=hashlib.sha256,
        ).hexdigest()
        signature_ok = hmac.compare_digest(expected_signature, signature)
    except Exception:
        signature_ok = False

    # Parse JSON
    try:
        data = json.loads(body.decode("utf-8"))
    except json.JSONDecodeError:
        data = {}

    # Log the event
    RzpWebhookEvent.objects.create(
        event=data.get("event", ""),
        payload=data,
        signature_ok=signature_ok,
    )

    if not signature_ok:
        print("Razorpay webhook: invalid signature")
        return HttpResponse("Invalid signature", status=400)

    event = data.get("event")
    payload = data.get("payload", {}) or {}

    print("== RAZORPAY WEBHOOK ==", event)

    # =========================================================
    # 1) subscription.activated → CREATE TenantRequest
    # =========================================================
    if event == "subscription.activated":
        # Razorpay: payload["subscription"]["entity"]["id"]
        sub_entity = payload.get("subscription", {}).get("entity", {}) or {}
        rzp_sub_id = sub_entity.get("id")

        print("subscription.activated → subscription_id from payload:", rzp_sub_id)

        if not rzp_sub_id:
            return HttpResponse(status=200)

        try:
            sub = RzpSubscription.objects.get(
                razorpay_subscription_id=rzp_sub_id
            )
        except RzpSubscription.DoesNotExist:
            print("No local RzpSubscription found for", rzp_sub_id)
            return HttpResponse(status=200)

        # Mark subscription active
        now = timezone.now()
        sub.status = "active"
        sub.started_at = now
        sub.current_period_start = now
        sub.current_period_end = (
            now + relativedelta(months=1)
            if sub.interval == "monthly"
            else now + relativedelta(years=1)
        )
        sub.save()

        # Map RzpPlan → SubscriptionPlan (optional)
        subscription_plan = None
        if sub.plan:
            subscription_plan = SubscriptionPlan.objects.filter(
                name__iexact=sub.plan.name.lower()
            ).first()

        payment_plan = "Monthly" if sub.interval == "monthly" else "Yearly"

        # 🔹 Create TenantRequest instead of Client
        tr = TenantRequest.objects.create(
            tenant_name=sub.tenant_name,
            desired_domain=sub.desired_domain,
            email=sub.email,
            plan=subscription_plan,
            brand_color= sub.brand_color,
            theme= sub.theme,
            payment_mode="CARD",      # online payment
            payment_plan=payment_plan,
            status="Pending",         # admin will approve later
        )

        print("TenantRequest created with id:", tr.id)
        return HttpResponse("TenantRequest created", status=200)

    # =========================================================
    # 2) payment.captured → update invoice + payment
    # =========================================================
    if event == "payment.captured":
        pay_entity = payload.get("payment", {}).get("entity", {}) or {}
        rzp_sub_id = pay_entity.get("subscription_id")

        print("payment.captured → subscription_id from payment:", rzp_sub_id)

        if not rzp_sub_id:
            # some test events have no subscription_id
            return HttpResponse(status=200)

        try:
            sub = RzpSubscription.objects.get(
                razorpay_subscription_id=rzp_sub_id
            )
        except RzpSubscription.DoesNotExist:
            print("No local RzpSubscription found for", rzp_sub_id)
            return HttpResponse(status=200)

        amount = pay_entity.get("amount", 0)
        razorpay_payment_id = pay_entity.get("id")

        # Get or create pending invoice
        inv = sub.invoices.filter(status="pending").order_by("created_at").first()
        if not inv:
            inv = RzpInvoice.objects.create(
                subscription=sub,
                invoice_number=_next_invoice_number(),
                amount_in_paise=amount,
                currency=pay_entity.get("currency", "INR"),
                status="pending",
            )

        # Create payment
        RzpPayment.objects.create(
            subscription=sub,
            invoice=inv,
            razorpay_payment_id=razorpay_payment_id,
            amount_in_paise=amount,
            currency=pay_entity.get("currency", "INR"),
            captured=True,
        )

        # Mark invoice paid
        inv.status = "paid"
        inv.paid_at = timezone.now()
        inv.save()

        print("Invoice marked paid for subscription:", rzp_sub_id)
        return HttpResponse("Payment updated", status=200)

    # Other events: just acknowledge
    return HttpResponse("OK", status=200)



# ====================================================================
#                        REFUND API
# ====================================================================

def refund_payment_view(request, payment_id: str):
    """
    Refunds a Razorpay payment via API.
    """
    try:
        rr = rzp_refund(payment_id)
        return JsonResponse({"ok": True, "refund": rr})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)



