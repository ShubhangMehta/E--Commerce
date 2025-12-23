# customers/rzp_services.py

"""
Razorpay Service Utilities
--------------------------

This module contains helper functions for interacting with the Razorpay API.
It includes:
    - Initializing Razorpay client
    - Creating or fetching subscription plans
    - Creating subscriptions
    - Canceling subscriptions
    - Processing refunds

All logic is preserved exactly as before — only improved readability and comments added.
"""

import razorpay
from django.conf import settings
<<<<<<< HEAD
=======
from django.utils import timezone

from .models import Client, SubscriptionPlan, ClientSubscription, Payment, Invoice

# Initialize Razorpay client
rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)
>>>>>>> 015d193 (webhook is remaining razorpay working.)


# -------------------------------------------------------------
# Razorpay Client Initialization
# -------------------------------------------------------------

def rzp():
    """
    Returns a Razorpay client instance using credentials from settings.
    """
    return razorpay.Client(
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
    )


# -------------------------------------------------------------
# Razorpay Plan Management
# -------------------------------------------------------------

def create_or_fetch_plan(plan):
    """
    Creates a Razorpay plan if not already created.

    Args:
        plan: Django model instance representing the subscription plan.
              Must contain interval, name, amount_in_paise, razorpay_plan_id.

    Returns:
        The Razorpay plan ID (existing or newly created).
    """

    # If plan already exists in Razorpay, return it
    if plan.razorpay_plan_id:
        return plan.razorpay_plan_id

<<<<<<< HEAD
    # Prepare payload for new Razorpay plan
    payload = {
        "period": "monthly" if plan.interval == "monthly" else "yearly",
        "interval": 1,   # Billing interval (1 month or 1 year)
        "item": {
            "name": f"{plan.name} ({plan.interval})",
            "amount": plan.amount_in_paise,
=======
    # 1) Create local Payment record (unpaid)
    payment = Payment.objects.create(
        client=client,
        amount=amount,
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
    #amount_in_paise = int(amount * 100)
    amount = int(plan.price)
    

    rzp_order = rzp_client.order.create(
        {
            "amount": amount * 100,
>>>>>>> dbe9696 (Payment system configured and working from tenant endpoint)
            "currency": "INR",
        },
    }

    # Create plan in Razorpay
    rzp_plan = rzp().plan.create(payload)

    # Save plan ID to local model
    plan.razorpay_plan_id = rzp_plan["id"]
    plan.save(update_fields=["razorpay_plan_id"])

    return rzp_plan["id"]


# -------------------------------------------------------------
# Razorpay Subscription Handling
# -------------------------------------------------------------

def create_subscription(plan, customer_notify=True):
    """
    Creates a new Razorpay subscription for the given plan.

    Args:
        plan: Django model instance of the subscription plan.
        customer_notify: Whether Razorpay should notify the customer by email/SMS.

    Returns:
        Razorpay subscription object.
    """

    plan_id = create_or_fetch_plan(plan)

    payload = {
        "plan_id": plan_id,
        "total_count": 1,            # One billing cycle
        "customer_notify": customer_notify,
        "expire_by": None,           # No auto-expiry
    }

    return rzp().subscription.create(payload)


def cancel_subscription(rzp_subscription_id, cancel_at_cycle_end=False):
    """
    Cancels an active Razorpay subscription.

    Args:
        rzp_subscription_id: ID of the Razorpay subscription.
        cancel_at_cycle_end: If True, cancel after current cycle ends;
                             If False, cancel immediately.

    Returns:
        Razorpay API response.
    """
    return rzp().subscription.cancel(
        rzp_subscription_id,
        {"cancel_at_cycle_end": cancel_at_cycle_end}
    )


# -------------------------------------------------------------
# Razorpay Refund Processing
# -------------------------------------------------------------

def refund_payment(payment_id, amount_in_paise=None):
    """
    Issues a refund for a payment.

    Args:
        payment_id: Razorpay payment ID.
        amount_in_paise: Optional partial refund amount in paise.
                         If None, it refunds full amount.

    Returns:
        Razorpay API refund response.
    """

    data = {}

    # If partial amount is specified, include it in the payload
    if amount_in_paise:
        data["amount"] = amount_in_paise

    return rzp().payment.refund(payment_id, data)
