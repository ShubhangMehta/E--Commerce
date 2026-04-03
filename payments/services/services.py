from decimal import Decimal
from django.utils import timezone
from django.db import transaction, connection

from orders.models import Order
from payments.models import OrderPayment
from notifications.services.services import safe_send_order_paid_email

def paise_to_rupees(amount_paise: int) -> Decimal:
    return Decimal(amount_paise) / Decimal("100")

def register_razorpay_payment_success(
        *,
        local_order_id,
        razorpay_order_id,
        razorpay_payment_id,
        razorpay_signature,
        payment_method,
        amount_paise,
        currency,
        raw_payload,
):
    schema_name = connection.schema_name

    with transaction.atomic():
        order = Order.objects.select_for_update().get(id=local_order_id)

        payment, created = OrderPayment.objects.get_or_create(
            razorpay_payment_id=razorpay_payment_id,
            defaults={
                "order": order,
                "razorpay_order_id": razorpay_order_id,
                "razorpay_signature": razorpay_signature,
                "status": "captured",
                "payment_method": payment_method,
                "amount": paise_to_rupees(amount_paise),
                "currency": currency,
                "paid_at": timezone.now(),
                "raw_payload": raw_payload,
            },
        )

        print(
            f"Payment record {'created' if created else 'already exists'} " 
            f"For Razorpay Payment ID: {razorpay_payment_id}"
        )

        update_fields = []

        if order.payment_status != "paid":
            order.payment_status = "paid"
            update_fields.append("payment_status")

        if order.status != "confirmed":
            order.status = "confirmed"
            update_fields.append("status")

        if update_fields:
            order.save(update_fields=update_fields)

        if not payment.confirmation_email_sent:
            transaction.on_commit(
                lambda schema_name=schema_name, order_pk=order.id, payment_id=payment.id:
                    safe_send_order_paid_email(
                        schema_name=schema_name,
                        order_id=order_pk,
                        payment_id=payment_id,
                    )
            )

        return payment