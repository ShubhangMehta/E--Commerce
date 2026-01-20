import hmac
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.shortcuts import redirect

from .models import Invoice, RzpPayment, RzpWebhookEvent
from .services.provisioning import provision_tenant_from_request

def verify_razorpay_signature(body: bytes, received_signature: str) -> bool:
    """
    Verify Razorpay webhook signature using RAZORPAY_WEBHOOK_SECRET.
    """
    if not received_signature:
        return False

    generated_signature = hmac.new(
        settings.RAZORPAY_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(generated_signature, received_signature)


@csrf_exempt
@transaction.atomic
def razorpay_webhook(request):
    
    raw_body = request.body

    signature = (
        request.headers.get("X-Razorpay-Signature")
        or request.META.get("HTTP_X_RAZORPAY_SIGNATURE")
    )

    if not verify_razorpay_signature(raw_body, signature):
        print("⚠️ Invalid Razorpay signature ⚠️")
        print("Signature received:", signature)
        return HttpResponseBadRequest("Invalid Razorpay signature")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except Exception:
        return HttpResponseBadRequest("Invalid JSON")

    print("🔥 RAZORPAY WEBHOOK VERIFIED 🔥")
    print(payload)

    event = payload.get("event", "")

    RzpWebhookEvent.objects.create(event=event, payload=payload)    #signature=signature,    

    entity = (payload.get("payload", {}) or {}).get("payment", {}).get("entity", {}) or {}
    rzp_order_id = entity.get("order_id")
    rzp_payment_id = entity.get("id")
    status = entity.get("status")  # captured/failed/authorized etc.
    amount = entity.get("amount")
    currency = entity.get("currency", "INR")
    failure_reason = entity.get("error_description") or ""

    if not rzp_order_id:
        return HttpResponseBadRequest("Missing order_id")

    invoice = Invoice.objects.select_for_update().filter(razorpay_order_id=rzp_order_id).first()
    if not invoice:
        return HttpResponseBadRequest("Invoice not found")

    # Idempotency: if already paid, ignore duplicates
    if invoice.status == "paid":
        return JsonResponse({"ok": True, "invoice_already_paid": True})

    # Idempotency: same payment_id should not create duplicates
    if rzp_payment_id and RzpPayment.objects.filter(razorpay_payment_id=rzp_payment_id).exists():
        return JsonResponse({"ok": True, "duplicate_payment_id": True})

    tr = invoice.tenant_request

    # Failed attempt: keep invoice as issued (so retry is allowed)
    if event == "payment.failed" or status == "failed":
        RzpPayment.objects.create(
            subscription=None,
            invoice=invoice,
            razorpay_payment_id=rzp_payment_id,
            razorpay_order_id=rzp_order_id,
            amount=(amount/100) or (invoice.amount/100),
            currency=currency,
            status="failed",
            event="payment.failed",
            captured=False,
            failure_reason=failure_reason,
            meta=payload,
        )
        return JsonResponse({"ok": True, "recorded_failed_attempt": True})

    # Captured: provision tenant and activate
    if event == "payment.captured" or status == "captured":
        tenant, domain, subscription = provision_tenant_from_request(
            tenant_request=tr, plan=tr.plan, pricing=tr.pricing
        )

        # Log captured payment
        RzpPayment.objects.create(
            subscription=subscription,
            invoice=invoice,
            razorpay_payment_id=rzp_payment_id,
            razorpay_order_id=rzp_order_id,
            amount=(amount/100) or (invoice.amount/100),
            currency=currency,
            status="captured",
            event="payment.captured",
            captured=True,
            meta=payload,
        )

        # Activate subscription using your method
        subscription.activate_from_payment()

        # Mark invoice paid and link tenant/subscription
        invoice.status = "paid"
        invoice.client = tenant
        invoice.subscription = subscription
        invoice.save(update_fields=["status", "client", "subscription"])

        # Mark request paid_created
        tr.status = "approved"
        tr.save(update_fields=["status"])

        return JsonResponse({"ok": True, "provisioned": True, "tenant_domain": domain.domain})
    
    # Other events can be recorded if you want (authorized, created)
    return JsonResponse({"ok": True, "ignored_event": event})

