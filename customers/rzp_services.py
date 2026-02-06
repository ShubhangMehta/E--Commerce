# customers/rzp_services.py

import razorpay
from django.conf import settings

from .models import Invoice

# Initialize Razorpay client
rzp_client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

def get_or_create_order_for_invoice(invoice: Invoice) -> dict:
    """
    Resume-same-invoice behavior:
    - If invoice already has razorpay_order_id, reuse it (client can retry).
    - Otherwise create a new Razorpay Order and save it on the invoice.
    """
    if invoice.razorpay_order_id:
        return {"id": invoice.razorpay_order_id}

    tr = invoice.tenant_request

    rzp_order = rzp_client.order.create({
        "amount": invoice.amount*100,           # paise
        "currency": invoice.currency,       # INR
        "payment_capture": 1,
        "receipt": invoice.invoice_number,
        "notes": {
            "invoice_id": str(invoice.id),
            "tenant_request_id": str(tr.id),
            "desired_domain": str(tr.desired_domain),
        },
    })

    invoice.razorpay_order_id = rzp_order["id"]
    invoice.save(update_fields=["razorpay_order_id"])

    return rzp_order


