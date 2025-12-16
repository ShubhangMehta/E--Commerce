import hmac
import hashlib
import json
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils import timezone

from .models import Payment, ClientSubscription, Invoice, RzpPayment, RzpWebhookEvent

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
def razorpay_webhook(request):
    """
    Handle Razorpay webhooks for subscription payments.
    """

    print("🔥 RAZORPAY WEBHOOK HIT 🔥")
    print(request.body)

    body = request.body
    received_signature = request.headers.get("X-Razorpay-Signature", "")

    # 1) Verify signature
    signature_ok = verify_razorpay_signature(body, received_signature)
    event_data = json.loads(body.decode("utf-8") or "{}")

    # 2) Store raw event
    RzpWebhookEvent.objects.create(
        event=event_data.get("event", "unknown"),
        payload=event_data,
        signature_ok=signature_ok,
    )

    if not signature_ok:
        return HttpResponseBadRequest("Invalid signature")

    event_type = event_data.get("event")

    # We care about payment.captured
    if event_type == "payment.captured":
        payment_entity = event_data["payload"]["payment"]["entity"]

        razorpay_payment_id = payment_entity["id"]
        razorpay_order_id = payment_entity.get("order_id")
        amount = payment_entity["amount"]
        currency = payment_entity.get("currency", "INR")

        # Notes we set when creating the order
        notes = payment_entity.get("notes", {})
        payment_id = notes.get("payment_id")
        subscription_id = notes.get("subscription_id")
        invoice_id = notes.get("invoice_id")

        # Try locating our Payment either via notes or via order_id
        try:
            if payment_id:
                payment = Payment.objects.get(id=payment_id)
            else:
                payment = Payment.objects.get(transaction_id=razorpay_order_id)
        except Payment.DoesNotExist:
            # We got a payment for which we can't find a record; log and exit
            return HttpResponse("Payment record not found", status=200)

        # 3) Mark Payment as paid
        payment.status = "paid"
        payment.save(update_fields=["status"])

        # 4) Update subscription if present
        subscription = None
        if subscription_id:
            try:
                subscription = ClientSubscription.objects.get(id=subscription_id)
            except ClientSubscription.DoesNotExist:
                subscription = None

        if subscription:
            # Ensure start/end dates and status are consistent
            # save() logic already handles duration / expiry
            subscription.status = "active"
            subscription.save()

        # 5) Mark Invoice if present
        invoice = None
        if invoice_id:
            try:
                invoice = Invoice.objects.get(id=invoice_id)
            except Invoice.DoesNotExist:
                invoice = None

        # 6) Create RzpPayment entry
        RzpPayment.objects.create(
            subscription=subscription,
            invoice=invoice,
            razorpay_payment_id=razorpay_payment_id,
            amount=amount/100,
            currency=currency,
            captured=True,
            meta=payment_entity,
        )

    # You can also add handling for payment.failed, refund.created, etc.
    return HttpResponse("OK", status=200)
