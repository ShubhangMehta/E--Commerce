import json
import hmac
import hashlib
import uuid

from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction

from .forms import CheckoutForm
from .models import Plan, Subscription, Invoice, Payment, WebhookEvent
from customers.models import Client, Domain
from .services import create_subscription as rzp_create_subscription, refund_payment as rzp_refund


def _next_invoice_number():
    base = settings.BILLING_INVOICE_PREFIX
    return f"{base}-{uuid.uuid4().hex[:10].upper()}"


def pricing_page(request):
    plans = Plan.objects.all().order_by("amount_in_paise")
    for p in plans:
        p.amount_in_rupees = p.amount_in_paise / 100
    return render(request, "billing/pricing.html", {
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID
    })


def checkout_view(request):
    form = CheckoutForm(request.GET or None)
    plans = Plan.objects.all().order_by("amount_in_paise")
    for p in plans:
        p.amount_in_rupees = p.amount_in_paise / 100
    return render(request, "billing/checkout.html", {
        "form": form,
        "plans": plans,
        "rzp_key": settings.RAZORPAY_KEY_ID
    })


@transaction.atomic
def start_subscription(request):
    try:
        if request.method != "POST":
            return HttpResponseBadRequest("POST required")

        desired_domain = (request.POST.get("domain") or "").strip().lower()
        email = (request.POST.get("email") or "").strip()
        plan_name = (request.POST.get("plan") or "").strip()
        interval = (request.POST.get("interval") or "").strip()

        if not desired_domain or not email or not plan_name or not interval:
            return JsonResponse({"ok": False, "error": "Missing required fields"}, status=400)

        # Auto-generate tenant name from domain
        tenant_name = desired_domain.replace("-", " ").title()

        try:
            plan = Plan.objects.get(name=plan_name, interval=interval)
        except Plan.DoesNotExist:
            return JsonResponse({"ok": False, "error": "Invalid plan or interval"}, status=400)

        if Domain.objects.filter(domain=f"{desired_domain}.localhost").exists():
            return JsonResponse({"ok": False, "error": "Domain already taken"}, status=400)

        sub = Subscription.objects.create(
            tenant_name=tenant_name,
            desired_domain=desired_domain,
            email=email,
            plan=plan,
            status="created",
        )

        # Create Razorpay subscription (must have total_count >= 1 in services.py)
        rzp_sub = rzp_create_subscription(plan)
        sub.razorpay_subscription_id = rzp_sub["id"]
        sub.status = "auth_pending"
        sub.save()

        # Proforma invoice; will be marked paid on webhook
        Invoice.objects.create(
            subscription=sub,
            number=_next_invoice_number(),
            amount_in_paise=plan.amount_in_paise,
            status="unpaid",
        )

        return JsonResponse({
            "ok": True,
            "subscription_id": rzp_sub["id"],
            "rzp_key": settings.RAZORPAY_KEY_ID
        })

    except Exception as e:
        import traceback
        traceback.print_exc()
        return JsonResponse({"ok": False, "error": str(e)}, status=500)


@csrf_exempt
def razorpay_webhook(request):
    # Validate signature
    body = request.body
    signature = request.headers.get("X-Razorpay-Signature", "")
    digest = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        msg=body,
        digestmod=hashlib.sha256
    ).hexdigest()

    signature_ok = hmac.compare_digest(digest, signature)
    data = {}
    try:
        payload = request.body.decode("utf-8") if request.body else ""
        data = json.loads(payload) if payload else {}
    except Exception:
        pass

    WebhookEvent.objects.create(
        event=data.get("event", ""),
        payload=data,
        signature_ok=signature_ok,
    )

    # Swallow invalid signatures (but record them)
    if not signature_ok:
        return HttpResponse(status=200)

    event = data.get("event")
    entity = data.get("payload", {}).get("subscription") or data.get("payload", {}).get("payment")

    # Handle subscription lifecycle events
    if event in ("subscription.activated", "subscription.charged", "subscription.halted", "subscription.completed"):
        sub_ent = (entity or {}).get("entity", {})
        rzp_sub_id = sub_ent.get("id")
        if not rzp_sub_id:
            return HttpResponse(status=200)

        try:
            # Lock row during update
            sub = Subscription.objects.select_for_update().get(razorpay_subscription_id=rzp_sub_id)
        except Subscription.DoesNotExist:
            return HttpResponse(status=200)

        # On first activation/charge → start period, create tenant if absent
        if event in ("subscription.activated", "subscription.charged"):
            now = timezone.now()
            if not sub.started_at:
                sub.started_at = now
            sub.status = "active"
            sub.mark_period(now)
            sub.save()

            # Mark latest unpaid invoice as paid; log payment if present
            inv = sub.invoices.order_by("-issued_at").first()
            if inv and inv.status != "paid":
                rzp_payment_id = None
                try:
                    rzp_payment_id = data["payload"]["payment"]["entity"]["id"]
                except Exception:
                    pass
                inv.status = "paid"
                inv.paid_at = now
                inv.razorpay_payment_id = rzp_payment_id
                inv.save()

                if rzp_payment_id:
                    Payment.objects.get_or_create(
                        subscription=sub,
                        razorpay_payment_id=rzp_payment_id,
                        defaults={"amount_in_paise": inv.amount_in_paise, "captured": True},
                    )

            # Create tenant schema if missing
            if not sub.client:
                client = Client.objects.create(
                    schema_name=sub.desired_domain,
                    tenant_name=sub.tenant_name,
                    server_name="primary",  # configure via settings if you prefer
                    desired_domain=sub.desired_domain,
                    plan_type=sub.plan.name,
                    subscription_start=now.date(),
                    subscription_end=sub.current_period_end.date(),
                    status="Active",
                    email=sub.email,
                )
                Domain.objects.create(
                    domain=f"{sub.desired_domain}.localhost",  # configure via settings if you prefer
                    tenant=client,
                    is_primary=True
                )
                sub.client = client
                sub.save()

        if event == "subscription.completed":
            sub.status = "expired"
            sub.cancelled_at = timezone.now()
            sub.save()

        return HttpResponse(status=200)

    # Handle payment.refunded → mark invoice refunded
    if event == "payment.refunded":
        pay_ent = (entity or {}).get("entity", {})
        rzp_payment_id = pay_ent.get("id")
        if not rzp_payment_id:
            return HttpResponse(status=200)

        try:
            payment = Payment.objects.get(razorpay_payment_id=rzp_payment_id)
        except Payment.DoesNotExist:
            return HttpResponse(status=200)

        payment.meta = entity
        payment.save()

        inv = payment.invoice or payment.subscription.invoices.filter(razorpay_payment_id=rzp_payment_id).first()
        if inv:
            inv.status = "refunded"
            inv.save()

        return HttpResponse(status=200)

    # Unknown or unhandled events are swallowed
    return HttpResponse(status=200)


def refund_payment_view(request, payment_id: str):
    try:
        rr = rzp_refund(payment_id)
        return JsonResponse({"ok": True, "refund": rr})
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=400)
