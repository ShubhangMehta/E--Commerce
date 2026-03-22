from decimal import Decimal
from time import time
import requests

from django.conf import settings
from customers.models import RazorpayOrderMap

def rupess_to_paise(amount: Decimal) -> int:
    return int(amount / 100)

class RazorpayGatewayError(Exception):
    pass    

def create_razorpay_order_for_order(*, tenant, order):
    amount_paise = rupess_to_paise(order.total_amount)

    payload = {
        "amount": amount_paise,
        "currency": "INR",
        "receipt": f"order_{order.id}_{int(time())}",
        "notes": {
            "tenant_schema": tenant.schema_name,
            "local_order_id": str(order.id),
        },
    }

    print("Razorpay KEY ID:", settings.RAZORPAY_KEY_ID)
    print("RAZORPAY PAYLOAD:", payload)

    response = requests.post(
        "https://api.razorpay.com/v1/orders",
        auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET),
        json=payload,
        timeout=20,
    )
    print("Razorpay Response Status:", response.status_code)
    print("Razorpay Response Body:", response.text)

    if response.status_code >= 400:
        raise RazorpayGatewayError(f"Failed to create Razorpay order: {response.status_code} {response.text}")
    
    #response.raise_for_status() Keep it for later
    data = response.json()

    RazorpayOrderMap.objects.create(
        razorpay_order_id=data["id"],
        tenant=tenant,
        local_order_id=order.id,
        local_order_number=str(order.id),
        amount_paise=data["amount"],
        currency=data["currency"],
        receipt=data.get("receipt", ""),
        status=data.get("status", "created"),
    )

    return data
