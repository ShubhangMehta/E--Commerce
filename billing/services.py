import razorpay
from django.conf import settings

def rzp():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def create_or_fetch_plan(plan):
    """
    If you want Razorpay-managed plans for Subscriptions, either
    set plan.razorpay_plan_id manually from dashboard OR create here.
    """
    if plan.razorpay_plan_id:
        return plan.razorpay_plan_id
    payload = {
        "period": "monthly" if plan.interval == "monthly" else "yearly",
        "interval": 1,
        "item": {
            "name": f"{plan.name} ({plan.interval})",
            "amount": plan.amount_in_paise,
            "currency": "INR",
        }
    }
    rp_plan = rzp().plan.create(payload)
    plan.razorpay_plan_id = rp_plan["id"]
    plan.save(update_fields=["razorpay_plan_id"])
    return plan.razorpay_plan_id

def create_subscription(plan, customer_notify=True):
    plan_id = create_or_fetch_plan(plan)
    payload = {
        "plan_id": plan_id,
        "total_count": 1,  # open-ended (autopay)
        "customer_notify": customer_notify,
        "expire_by": None
    }
    return rzp().subscription.create(payload)

def cancel_subscription(rzp_subscription_id, cancel_at_cycle_end=False):
    return rzp().subscription.cancel(rzp_subscription_id, {"cancel_at_cycle_end": cancel_at_cycle_end})

def refund_payment(payment_id, amount_in_paise=None):
    data = {}
    if amount_in_paise:
        data["amount"] = amount_in_paise
    return rzp().payment.refund(payment_id, data)
