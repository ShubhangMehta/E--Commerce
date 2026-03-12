from decimal import Decimal
import requests

from django.conf import settings
from customers.models import RazorpayOrderMap

def rupess_to_paise(amount: Decimal) -> int:
    return int(amount * 100)

def create_razorpay_order_for_order(*, tenant, order):
    amount_paise = rupess_to_paise(order.total_amount)

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"E-Cartel - {tenant.schema_name} - Order #{order.id}",
        "notes": {
            "tenant_schema": tenant.schema_name,
            "local_order_id": str(order.id),
        },
    }

    response = requests.post(
        "https://api.razorpay.com/v1/orders",
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
        json=payload,
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()

    RazorpayOrderMap.objects.create(
        razorpay_order_id=data["id"],
        defaults={
            "tenant": tenant,
            "local_order_id": order.id,
            "local_order_number": str(order.id),
            "amount_paise": data["amount"],
            "currency": data["currency"],
            "receipt": data.get("receipt", ""),
            "status": data.get("status", "created"),
        },
    )

    return data
