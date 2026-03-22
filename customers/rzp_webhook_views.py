import hmac
import hashlib
import json

from django.conf import settings
from django.http import JsonResponse, HttpResponseBadRequest
from django.db import transaction
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .models import Invoice, RzpPayment, RzpWebhookEvent, RazorpayOrderMap
from django_tenants.utils import tenant_context
from payments.services.services import register_razorpay_payment_success
from .services.provisioning import provision_tenant_from_request
from core_app.emails.utils import send_html_email

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
        tenant, domain, subscription, username, temp_password = provision_tenant_from_request(
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

        # Send welcome email to tenant owner
        try:
            send_html_email(
                subject="Your Store Is Ready",
                to_email=tr.email,
                template_name="emails/tenant_created.html",
                context={
                    "owner_name": tr.owner_name,
                    "tenant_name": tenant.tenant_name,
                    "company": tr.company,
                    "domain": domain,
                    "plan": tr.plan.name,
                    "email": tr.email,
                    "order_id": rzp_payment_id,
                    "amount": amount/100,
                    "currency": currency,
                    "billing_cycle": tr.pricing.billing_cycle,
                    "duration": tr.pricing.duration_days,
                    "username": username,
                    "end_date": subscription.end_date,
                    "subscription_type": "Trial" if subscription.is_trial else "Paid",
                    "login_url": f"https://{domain.domain}/login/",
                    "dashboard_url": f"https://{domain.domain}/dashboard/",
                    "temp_password": temp_password,
                    "is_trial": subscription.is_trial,
                    "order_id": tr.id,
                    #"trial_days": settings.BILLING_TRIAL_DAYS,
                    "trial_days": (subscription.end_date - subscription.start_date).days if subscription.is_trial else 7,
                }
            )
        except Exception:
            pass

        print("Tenant provisioned and payment recorded for tenant_request_id:", tr.id, "tenant_domain:", domain.domain, "✅")
        print("Email sent from webhook:", tr.email)


        return JsonResponse({"ok": True, "provisioned": True, "tenant_domain": domain.domain})
    
    # Other events can be recorded if you want (authorized, created)
    return JsonResponse({"ok": True, "ignored_event": event})


@method_decorator(csrf_exempt, name="dispatch")
class TenantRazorpayWebhookAPIView(APIView):
    authentication_classes = []  # No auth, relies on signature
    permission_classes = [AllowAny]      # No permissions, relies on signature

    def post(self, request):
        raw_body = request.body
        received_signature = request.headers.get("X-Razorpay-Signature", "")

        expected_signature = hmac.new(
            key=settings.RAZORPAY_WEBHOOK_SECRET.encode(),
            msg=raw_body,
            digestmod=hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(expected_signature, received_signature):
            print("⚠️ Invalid Razorpay signature ⚠️")
            print("Expected signature:", expected_signature)
            print("Received signature:", received_signature)
            return JsonResponse({"detail": "Invalid signature"}, status=400)
        
        payload = json.loads(raw_body.decode("utf-8"))
        event = payload.get("event")
        print(f"Received Razorpay webhook event: {event}")

        if event not in ["order.paid", "payment.captured"]:
            print(f"Ignoring unsupported event type: {event}")
            return JsonResponse({"detail": "Event ignored"}, status=200)
        
        payment_entity = payload["payload"]["payment"]["entity"]
        razorpay_order_id = payment_entity["order_id"]
        print(f"Processing payment for Razorpay Order ID: {razorpay_order_id}")

        try:
            order_map = RazorpayOrderMap.objects.select_related("tenant").get(razorpay_order_id=razorpay_order_id)
        except RazorpayOrderMap.DoesNotExist:
            return JsonResponse({"detail": "Order not found"}, status=404)
        
        with tenant_context(order_map.tenant):
            register_razorpay_payment_success(
                local_order_id=order_map.local_order_id,
                razorpay_order_id=payment_entity["order_id"],
                razorpay_payment_id=payment_entity["id"],
                razorpay_signature="",
                payment_method=payment_entity.get("method", ""),
                amount_paise=payment_entity["amount"],
                currency=payment_entity.get("currency", "INR"),
                raw_payload=payload,
            )

        return JsonResponse({"status": "ok"}, status=200)