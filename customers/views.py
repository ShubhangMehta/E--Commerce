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

import hmac
import hashlib
import uuid
import json
from datetime import timedelta
from dateutil.relativedelta import relativedelta

<<<<<<< HEAD
<<<<<<< HEAD
=======
# --------------------------------------------------------------------
# Models
# --------------------------------------------------------------------
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
from .models import (
    SubscriptionPlan,
    UserSubscription,
    UserInvoice,
    UserPayment,
    UserRefundRequest,
    RzpPlan,
    RzpSubscription,
    RzpInvoice,
    RzpPayment,
    RzpWebhookEvent,
    Client,
    Domain,
)

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

def home(request):
    """Public landing page showing available plans."""
    plans = SubscriptionPlan.objects.filter(status='active')
<<<<<<< HEAD
=======
# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Plan, Subscription, Invoice, Payment, Refund
from django.utils import timezone
import json


def home(request):
    plans = Plan.objects.filter(is_active=True)
>>>>>>> 0078471 (mylatestcode)
    return render(request, 'billing/home.html', {'plans': plans})


def plans(request):
<<<<<<< HEAD
=======
    return render(request, 'home.html', {'plans': plans})


def plans(request):
    """Plan listing page."""
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
    plans = SubscriptionPlan.objects.filter(status='active')
    return render(request, 'billing/plans.html', {'plans': plans})


@login_required
def billing_cycle(request):
    """
    Shows all subscriptions and related invoices for the logged-in user.
    """
    subscriptions = UserSubscription.objects.filter(user=request.user)
<<<<<<< HEAD
=======
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'billing/plans.html', {'plans': plans})

def billing_cycle(request):
    subscriptions = Subscription.objects.filter(tenant__user=request.user)
>>>>>>> 0078471 (mylatestcode)
    invoices = Invoice.objects.filter(subscription__in=subscriptions)
=======
    invoices = UserInvoice.objects.filter(subscription__in=subscriptions)

>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
    return render(request, 'billing/billing_cycle.html', {
        'subscriptions': subscriptions,
        'invoices': invoices
    })

<<<<<<< HEAD

@login_required
def checkout(request, plan_id):
    """
    Checkout page: creates subscription + payment + invoice.
    """
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    if request.method == 'POST':

        # Create user subscription
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=plan.duration_days),
        )

        # Create payment entry
        payment = UserPayment.objects.create(
            user=request.user,
            amount=plan.price,
            method='upi',
            payment_plan='monthly',
            transaction_id=str(uuid.uuid4()),
            status='paid'
        )

        # Create invoice
        invoice = UserInvoice.objects.create(
            user=request.user,
            subscription=subscription,
            payment=payment,
            invoice_number=str(uuid.uuid4())[:12],
            invoice_type='auto'
        )

        return redirect('payment_success', invoice_id=invoice.id)

    return render(request, 'billing/checkout.html', {'plan': plan})


=======
@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    if request.method == 'POST':
        # Process payment and create subscription
        subscription = Subscription.objects.create(
            tenant=request.user.tenant,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            next_due_date=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Create invoice
        invoice = Invoice.objects.create(
            subscription=subscription,
            amount=plan.price,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        return redirect('payment_success', invoice_id=invoice.id)
    
    return render(request, 'billing/checkout.html', {'plan': plan})

>>>>>>> 0078471 (mylatestcode)
@login_required
def payment_success(request, invoice_id):
    """Payment success page."""
    invoice = get_object_or_404(UserInvoice, id=invoice_id)
    return render(request, 'billing/payment_success.html', {'invoice': invoice})

<<<<<<< HEAD

@login_required
def subscription(request):
    """Shows active user subscriptions."""
    subscriptions = UserSubscription.objects.filter(user=request.user)
    return render(request, 'billing/subscription.html', {'subscriptions': subscriptions})


@login_required
def renew_subscription(request, subscription_id):
    """
    Renews an existing subscription and generates invoice.
    """
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)

    if request.method == 'POST':

        # Record payment
        payment = UserPayment.objects.create(
            user=request.user,
            amount=subscription.plan.price,
            method='upi',
            payment_plan='monthly',
            transaction_id=str(uuid.uuid4()),
            status='paid'
        )

        # Generate invoice
        invoice = UserInvoice.objects.create(
            user=request.user,
            subscription=subscription,
            payment=payment,
            invoice_number=str(uuid.uuid4())[:12],
            invoice_type='auto'
        )

        return redirect('payment_success', invoice_id=invoice.id)

    return render(request, 'billing/renew.html', {'subscription': subscription})


@login_required
def update_plan(request, subscription_id):
    """
    AJAX API: update user subscription plan.
    """
    if request.method == 'POST':
        data = json.loads(request.body)

        subscription = get_object_or_404(UserSubscription, id=subscription_id)
        new_plan = get_object_or_404(SubscriptionPlan, id=data['plan_id'])

        subscription.plan = new_plan
        subscription.save()

        return JsonResponse({'success': True, 'message': 'Plan updated successfully'})


@login_required
def mark_invoice_paid(request, invoice_id):
    """
    Marks an invoice as manually paid (admin).
    """
    invoice = get_object_or_404(UserInvoice, id=invoice_id)

    invoice.payment.status = 'paid'
    invoice.payment.save()

    return JsonResponse({'success': True, 'message': 'Invoice marked as paid'})


<<<<<<< HEAD
<<<<<<< HEAD
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
=======
# ---------------------------------------------
#  Razorpay Billing Views (moved from billing app)
# ---------------------------------------------
=======
# ====================================================================
#                        RAZORPAY BILLING VIEWS
# ====================================================================
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)

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

    return render(request, "billing/pricing.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID,
    })


@transaction.atomic
def start_subscription(request):
    """
    Starts Razorpay subscription and creates local DB entries.
    """
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    # Extract form fields
    desired_domain = (request.POST.get("domain") or "").strip().lower()
    email = (request.POST.get("email") or "").strip()
    plan_name = (request.POST.get("plan") or "").strip()
    interval = (request.POST.get("interval") or "").strip()

    if not all([desired_domain, email, plan_name, interval]):
        return JsonResponse({"ok": False, "error": "Missing fields"}, status=400)

    tenant_name = desired_domain.replace("-", " ").title()

    # Fetch plan
    try:
        plan = RzpPlan.objects.get(name=plan_name, interval=interval)
    except RzpPlan.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid plan"}, status=400)

    # Create Razorpay subscription
    rzp_sub = rzp_create_subscription(plan, customer_notify=True)

    # Store subscription
    sub = RzpSubscription.objects.create(
        tenant_name=tenant_name,
        desired_domain=desired_domain,
        email=email,
        plan=plan,
        interval=interval,
        status="created",
        razorpay_subscription_id=rzp_sub["id"],
    )

    # Initial invoice (pending)
    invoice = RzpInvoice.objects.create(
        subscription=sub,
        invoice_number=_next_invoice_number(),
        amount_in_paise=plan.amount_in_paise,
        currency="INR",
        status="pending",
    )

    return JsonResponse({
        "ok": True,
        "subscription_id": sub.id,
        "razorpay_subscription_id": sub.razorpay_subscription_id,
        "invoice_number": invoice.invoice_number,
        "amount_in_paise": invoice.amount_in_paise,
        "razorpay_plan_id": plan.razorpay_plan_id,
        "rzp": rzp_sub,
    })


def checkout_view(request):
    """Alternate Razorpay checkout page."""
    plans = RzpPlan.objects.all().order_by("amount_in_paise")
    return render(request, "billing/checkout.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID,
    })


# ====================================================================
#                        RAZORPAY WEBHOOK HANDLER
# ====================================================================

@csrf_exempt
def razorpay_webhook(request):
    """
    Receives real-time subscription + payment events from Razorpay.
    """
    body = request.body
    signature = request.headers.get("X-Razorpay-Signature", "")

    # Verify signature
    digest = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    signature_ok = hmac.compare_digest(digest, signature)

    # Parse JSON safely
    try:
        payload = request.body.decode("utf-8") if request.body else "{}"
        data = json.loads(payload)
    except:
        data = {}

    # Log all webhook events
    RzpWebhookEvent.objects.create(
        event=data.get("event", ""),
        payload=data,
        signature_ok=signature_ok,
    )

    if not signature_ok:
        return HttpResponse(status=400)

    event = data.get("event")
    payload = data.get("payload", {})

    # -----------------------------
    # SUBSCRIPTION ACTIVATED
    # -----------------------------
    if event == "subscription.activated":
        sub_ent = payload.get("subscription", {})
        rzp_sub_id = sub_ent.get("id")

        try:
            sub = RzpSubscription.objects.get(razorpay_subscription_id=rzp_sub_id)
        except RzpSubscription.DoesNotExist:
            return HttpResponse(status=200)

        # Activate subscription
        now = timezone.now()
        sub.status = "active"
        sub.started_at = now
        sub.current_period_start = now
        sub.current_period_end = now + (relativedelta(months=1) if sub.interval == "monthly" else relativedelta(years=1))
        sub.save()

        # Create tenant if first-time subscription
        client, created = Client.objects.get_or_create(
            desired_domain=sub.desired_domain,
            defaults={
                "tenant_name": sub.tenant_name,
                "server_name": "default-server",
            },
        )

        if created:
            # Assign domain
            Domain.objects.create(
                domain=f"{sub.desired_domain}.localhost",
                tenant=client,
                is_primary=True,
            )

        sub.client = client
        sub.save()

    # -----------------------------
    # PAYMENT CAPTURED
    # -----------------------------
    if event == "payment.captured":
        pay_ent = payload.get("payment", {})
        rzp_sub_id = pay_ent.get("subscription_id")
        amount = pay_ent.get("amount", 0)

        try:
            sub = RzpSubscription.objects.get(razorpay_subscription_id=rzp_sub_id)
        except RzpSubscription.DoesNotExist:
            return HttpResponse(status=200)

        # Match pending invoice
        inv = sub.invoices.filter(status="pending").order_by("created_at").first()
        if not inv:
            inv = RzpInvoice.objects.create(
                subscription=sub,
                invoice_number=_next_invoice_number(),
                amount_in_paise=amount,
                currency="INR",
                status="pending",
            )

        # Record payment
        RzpPayment.objects.create(
            subscription=sub,
            invoice=inv,
            razorpay_payment_id=pay_ent.get("id"),
            amount_in_paise=amount,
            currency="INR",
            captured=True,
        )

        # Mark invoice paid
        inv.status = "paid"
        inv.paid_at = timezone.now()
        inv.save()

    return HttpResponse(status=200)


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
>>>>>>> 777f33b (razorpay integrated in coutomers folder)
=======
@login_required
def subscription(request):
    subscriptions = Subscription.objects.filter(tenant__user=request.user)
    return render(request, 'billing/subscription.html', {'subscriptions': subscriptions})

@login_required
def renew_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id, tenant__user=request.user)
    
    if request.method == 'POST':
        # Process renewal payment
        invoice = Invoice.objects.create(
            subscription=subscription,
            amount=subscription.plan.price,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        return redirect('payment_success', invoice_id=invoice.id)
    
    return render(request, 'billing/renew.html', {'subscription': subscription})

def update_plan(request, subscription_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        subscription = get_object_or_404(Subscription, id=subscription_id)
        new_plan = get_object_or_404(Plan, id=data['plan_id'])
        
        subscription.plan = new_plan
        subscription.save()
        
        return JsonResponse({'success': True, 'message': 'Plan updated successfully'})

def mark_invoice_paid(request, invoice_id):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, id=invoice_id)
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.save()
        
        return JsonResponse({'success': True, 'message': 'Invoice marked as paid'})
        
>>>>>>> 0078471 (mylatestcode)
