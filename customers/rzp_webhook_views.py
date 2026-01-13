import hmac
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction

from .models import ClientSubscription, Invoice, RzpPayment, RzpWebhookEvent
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
            amount=amount or invoice.amount,
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
            amount=amount or invoice.amount,
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


# @csrf_exempt
# def razorpay_webhook(request):
#     """
#     Handle Razorpay webhooks for subscription payments.
#     """

#     print("🔥 RAZORPAY WEBHOOK HIT 🔥")
#     print(request.body)

#     body = request.body
#     received_signature = request.headers.get("X-Razorpay-Signature", "")

#     # 1) Verify signature
#     signature_ok = verify_razorpay_signature(body, received_signature)
#     event_data = json.loads(body.decode("utf-8") or "{}")

#     # 2) Store raw event
#     RzpWebhookEvent.objects.create(
#         event=event_data.get("event", "unknown"),
#         payload=event_data,
#         signature_ok=signature_ok,
#     )

#     if not signature_ok:
#         return HttpResponseBadRequest("Invalid signature")

#     event_type = event_data.get("event")

#     # We care about payment.captured
#     if event_type == "payment.captured":
#         payment_entity = event_data["payload"]["payment"]["entity"]

#         razorpay_payment_id = payment_entity["id"]
#         razorpay_order_id = payment_entity.get("order_id")
#         amount = payment_entity["amount"]
#         currency = payment_entity.get("currency", "INR")

#         # Notes we set when creating the order
#         notes = payment_entity.get("notes", {})
#         payment_id = notes.get("payment_id")
#         subscription_id = notes.get("subscription_id")
#         invoice_id = notes.get("invoice_id")

#         # Try locating our Payment either via notes or via order_id
#         try:
#             if payment_id:
#                 payment = Payments.objects.get(id=payment_id)
#             else:
#                 payment = Payments.objects.get(transaction_id=razorpay_order_id)
#         except Payment.DoesNotExist:
#             # We got a payment for which we can't find a record; log and exit
#             return HttpResponse("Payment record not found", status=200)

#         # 3) Mark Payment as paid
#         payment.status = "paid"
#         payment.save(update_fields=["status"])

#         # 4) Update subscription if present
#         subscription = None
#         if subscription_id:
#             try:
#                 subscription = ClientSubscription.objects.get(id=subscription_id)
#             except ClientSubscription.DoesNotExist:
#                 subscription = None

#         if subscription:
#             # Ensure start/end dates and status are consistent
#             # save() logic already handles duration / expiry
#             subscription.status = "active"
#             subscription.save()

#         # 5) Mark Invoice if present
#         invoice = None
#         if invoice_id:
#             try:
#                 invoice = Invoice.objects.get(id=invoice_id)
#             except Invoice.DoesNotExist:
#                 invoice = None

#         # 6) Create RzpPayment entry
#         RzpPayment.objects.create(
#             subscription=subscription,
#             invoice=invoice,
#             razorpay_payment_id=razorpay_payment_id,
#             amount=amount/100,
#             currency=currency,
#             captured=True,
#             meta=payment_entity,
#         )

#     # You can also add handling for payment.failed, refund.created, etc.
#     return HttpResponse("OK", status=200)
