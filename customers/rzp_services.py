# customers/rzp_services.py

import razorpay
from django.conf import settings
from django.utils import timezone

from .models import Client, SubscriptionPlan, ClientSubscription, Payment, Invoice

# Initialize Razorpay client
rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)


def create_subscription_checkout(client: Client, plan: SubscriptionPlan, payment_plan: str = "Monthly"):
    """
    Create a Razorpay 'order' and corresponding local Payment / ClientSubscription / Invoice records.

    payment_plan: "Monthly" or "Yearly" (matches TenantRequest.PAYMENT_PLANS choices)
    """

    # Determine amount based on monthly/yearly
    if payment_plan.lower() == "yearly" and plan.duration_days == 30:
        # Simple example: 12x monthly price; you can adjust
        amount = plan.price * 12
    else:
        amount = plan.price

    # 1) Create local Payment record (unpaid)
    payment = Payment.objects.create(
        client=client,
        amount=amount,
        method="UPI",                # or "CARD" or dynamic, your choice
        payment_plan=payment_plan,
        transaction_id="",           # will fill with Razorpay order_id
        status="unpaid",
    )

    # 2) Create or update ClientSubscription
    subscription = ClientSubscription.objects.create(
        client=client,
        plan=plan,
        payment=payment,
        # start_date/end_date will be set in save()
        status="active",
        auto_renew=False,
    )

    # 3) Create invoice
    invoice = Invoice.objects.create(
        client=client,
        subscription=subscription,
        payment=payment,
        invoice_number=f"INV-{client.id}-{payment.id}",
        invoice_type="auto",
    )

    # 4) Create Razorpay Order (amount in paise)
    amount_in_paise = int(amount * 100)

    rzp_order = rzp_client.order.create(
        {
            "amount": amount_in_paise,
            "currency": "INR",
            "payment_capture": 1,
            "notes": {
                "client_id": client.id,
                "subscription_id": subscription.id,
                "payment_id": payment.id,
                "invoice_id": invoice.id,
            },
        }
    )

    razorpay_order_id = rzp_order["id"]

    # Store Razorpay order id in Payment.transaction_id
    payment.transaction_id = razorpay_order_id
    payment.save(update_fields=["transaction_id"])

    return {
        "razorpay_order": rzp_order,
        "subscription": subscription,
        "payment": payment,
        "invoice": invoice,
    }
