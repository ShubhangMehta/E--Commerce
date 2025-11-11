from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest  # already partly present
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.db import transaction
import hmac
import hashlib
import uuid
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from django.contrib.auth.decorators import login_required
import json

<<<<<<< HEAD
from .models import (
    SubscriptionPlan,
    UserSubscription,
    Invoice,
    Payment,
    RzpPlan,
    RzpSubscription,
    RzpInvoice,
    RzpPayment,
    RzpWebhookEvent,
)
from .rzp_services import create_subscription as rzp_create_subscription, refund_payment as rzp_refund
from .models import Client, Domain  # same app, but explicit



def home(request):
    plans = SubscriptionPlan.objects.filter(status='active')
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
    plans = SubscriptionPlan.objects.filter(status='active')
    return render(request, 'billing/plans.html', {'plans': plans})


@login_required
def billing_cycle(request):
    subscriptions = UserSubscription.objects.filter(user=request.user)
=======
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'billing/plans.html', {'plans': plans})

def billing_cycle(request):
    subscriptions = Subscription.objects.filter(tenant__user=request.user)
>>>>>>> 0078471 (mylatestcode)
    invoices = Invoice.objects.filter(subscription__in=subscriptions)
    return render(request, 'billing/billing_cycle.html', {
        'subscriptions': subscriptions,
        'invoices': invoices
    })

<<<<<<< HEAD

@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    if request.method == 'POST':

        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=plan.duration_days),
        )

        # Create payment
        payment = Payment.objects.create(
            user=request.user,
            amount=plan.price,
            method='upi',
            payment_plan='monthly',
            transaction_id=str(uuid.uuid4()),
            status='paid'
        )

        # Create invoice
        invoice = Invoice.objects.create(
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
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'billing/payment_success.html', {'invoice': invoice})

<<<<<<< HEAD

@login_required
def subscription(request):
    subscriptions = UserSubscription.objects.filter(user=request.user)
    return render(request, 'billing/subscription.html', {'subscriptions': subscriptions})


@login_required
def renew_subscription(request, subscription_id):
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        
        payment = Payment.objects.create(
            user=request.user,
            amount=subscription.plan.price,
            method='upi',
            payment_plan='monthly',
            transaction_id=str(uuid.uuid4()),
            status='paid'
        )

        invoice = Invoice.objects.create(
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
    if request.method == 'POST':
        data = json.loads(request.body)

        subscription = get_object_or_404(UserSubscription, id=subscription_id)
        new_plan = get_object_or_404(SubscriptionPlan, id=data['plan_id'])

        subscription.plan = new_plan
        subscription.save()

        return JsonResponse({'success': True, 'message': 'Plan updated successfully'})


@login_required
def mark_invoice_paid(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)

    invoice.payment.status = 'paid'
    invoice.payment.save()

    return JsonResponse({'success': True, 'message': 'Invoice marked as paid'})


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

def _next_invoice_number():
    base = getattr(settings, "BILLING_INVOICE_PREFIX", "INV")
    return f"{base}-{uuid.uuid4().hex[:10].upper()}"


def pricing_page(request):
    plans = RzpPlan.objects.all().order_by("amount_in_paise")
    for p in plans:
        p.amount_in_rupees = p.amount_in_paise / 100
    return render(request, "billing/pricing.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID,
    })


@transaction.atomic
def start_subscription(request):
    if request.method != "POST":
        return HttpResponseBadRequest("POST required")

    desired_domain = (request.POST.get("domain") or "").strip().lower()
    email = (request.POST.get("email") or "").strip()
    plan_name = (request.POST.get("plan") or "").strip()
    interval = (request.POST.get("interval") or "").strip()

    if not desired_domain or not email or not plan_name or not interval:
        return JsonResponse({"ok": False, "error": "Missing required fields"}, status=400)

    tenant_name = desired_domain.replace("-", " ").title()

    try:
        plan = RzpPlan.objects.get(name=plan_name, interval=interval)
    except RzpPlan.DoesNotExist:
        return JsonResponse({"ok": False, "error": "Invalid plan/interval"}, status=400)

    rzp_sub = rzp_create_subscription(plan, customer_notify=True)

    sub = RzpSubscription.objects.create(
        tenant_name=tenant_name,
        desired_domain=desired_domain,
        email=email,
        plan=plan,
        interval=interval,
        status="created",
        razorpay_subscription_id=rzp_sub["id"],
    )

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
    # Optional legacy/extra page if you still want it
    plans = RzpPlan.objects.all().order_by("amount_in_paise")
    return render(request, "billing/checkout.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID,
    })


@csrf_exempt
def razorpay_webhook(request):
    body = request.body
    signature = request.headers.get("X-Razorpay-Signature", "")

    digest = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    signature_ok = hmac.compare_digest(digest, signature)

    data = {}
    try:
        payload = request.body.decode("utf-8") if request.body else ""
        data = json.loads(payload) if payload else {}
    except Exception:
        pass

    RzpWebhookEvent.objects.create(
        event=data.get("event", ""),
        payload=data,
        signature_ok=signature_ok,
    )

    if not signature_ok:
        return HttpResponse(status=400)

    event = data.get("event")
    payload = data.get("payload", {})

    if event == "subscription.activated":
        sub_ent = payload.get("subscription", {})
        rzp_sub_id = sub_ent.get("id")
        try:
            sub = RzpSubscription.objects.get(razorpay_subscription_id=rzp_sub_id)
        except RzpSubscription.DoesNotExist:
            return HttpResponse(status=200)

        now = timezone.now()
        sub.status = "active"
        sub.started_at = now
        sub.current_period_start = now
        sub.current_period_end = now + relativedelta(months=1 if sub.interval == "monthly" else years=1)
        sub.save()

        client, created = Client.objects.get_or_create(
            desired_domain=sub.desired_domain,
            defaults={
                "tenant_name": sub.tenant_name,
                "server_name": "default-server",
            },
        )

        if created:
            Domain.objects.create(
                domain=f"{sub.desired_domain}.localhost",
                tenant=client,
                is_primary=True,
            )
        sub.client = client
        sub.save()

    if event == "payment.captured":
        pay_ent = payload.get("payment", {})
        rzp_sub_id = pay_ent.get("subscription_id")
        rzp_payment_id = pay_ent.get("id")
        amount = pay_ent.get("amount", 0)

        try:
            sub = RzpSubscription.objects.get(razorpay_subscription_id=rzp_sub_id)
        except RzpSubscription.DoesNotExist:
            return HttpResponse(status=200)

        inv = sub.invoices.filter(status="pending").order_by("created_at").first()
        if not inv:
            inv = RzpInvoice.objects.create(
                subscription=sub,
                invoice_number=_next_invoice_number(),
                amount_in_paise=amount,
                currency="INR",
                status="pending",
            )

        RzpPayment.objects.create(
            subscription=sub,
            invoice=inv,
            razorpay_payment_id=rzp_payment_id,
            amount_in_paise=amount,
            currency="INR",
            captured=True,
        )

        inv.status = "paid"
        inv.paid_at = timezone.now()
        inv.save()

    # handle refund events similarly if needed...

    return HttpResponse(status=200)


def refund_payment_view(request, payment_id: str):
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
