from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import select_template
from django.utils import timezone
from django.db import connection

from customers.models import Client
from orders.models import Order
from payments.models import OrderPayment
from notifications.models import EmailNotification

def render_order_paid_email(*, tenant, context):
    html_tpl = select_template([
        f"themes/{tenant.theme}/emails/order_paid.html",
        "themes/default/emails/order_paid.html",
    ])
    text_tpl = select_template([
        f"themes/{tenant.theme}/emails/order_paid.txt",
        "themes/default/emails/order_paid.txt",
    ])
    print(f"Selected HTML template for tenant '{tenant.schema_name}': {html_tpl.template.name}")
    print(f"Selected Text template for tenant '{tenant.schema_name}': {text_tpl.template.name}")
    return html_tpl.render(context), text_tpl.render(context)

def send_order_paid_email(*, order_id, payment_id):
    order = Order.objects.prefetch_related("items").get(id=order_id)
    payment = OrderPayment.objects.get(id=payment_id)

    notif, created = EmailNotification.objects.get_or_create(
        event="order_paid",
        order=order,
        payment=payment,
        defaults={
            "to_email": order.customer_email,
            "subject": f"Payment received for Order #{order.id}",
        },
    )

    if not created and notif.status == "sent":
        return

    items = []
    for item in order.items.all():
        items.append({
            "name": item.product_name_snapshot,
            "qty": item.quantity,
            "unit_price": item.product_price_snapshot,
            "line_total": item.line_total,
            "image_url": item.product_image_url_snapshot,
        })

    tenant_obj = None
    # If you keep tenant name only as schema context, pass tenant separately if needed.
    # For now, use request.tenant-backed branding via selected templates.

    context = {
        "order": order,
        "payment": payment,
        "items": items,
        "subtotal_amount": order.subtotal_amount,
        "shipping_amount": order.shipping_amount,
        "discount_amount": order.discount_amount,
        "total_amount": order.total_amount,
        "payment_reference_number": payment.razorpay_payment_id,
        "payment_method": payment.payment_method,
        "paid_at": payment.paid_at,
    }

    print(f"Preparing to send order_paid email for Order ID: {order.id}, Payment ID: {payment.id}, Tenant: {tenant_obj.schema_name if tenant_obj else 'N/A'}")

    # If your email theme depends on tenant.theme, pass the tenant object into this function.
    # For now, assume you can obtain it from current tenant context or order snapshot.
    
    tenant_obj = Client.objects.get(schema_name=connection.schema_name)

    html_body, text_body = render_order_paid_email(tenant=tenant_obj, context=context)

    msg = EmailMultiAlternatives(
        subject=notif.subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[notif.to_email],
    )
    msg.attach_alternative(html_body, "text/html")
    msg.send()

    notif.status = "sent"
    notif.sent_at = timezone.now()
    notif.payload_snapshot = context
    notif.error_message = ""
    notif.save(update_fields=["status", "sent_at", "payload_snapshot", "error_message"])