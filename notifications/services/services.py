from django.conf import settings
from django.db import connection
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, select_template
from django.utils import timezone
from django_tenants.utils import tenant_context

from orders.models import Order
from payments.models import OrderPayment
from payments.services.invoice_service import build_invoice_pdf_bytes
    
def get_order_confirmation_template(tenant):
    theme = getattr(tenant, "theme", "default") if tenant else "default"

    template = select_template([
        f"themes/{theme}/emails/order_confirmation.html",
    ])
    return template.template.name


def safe_send_order_paid_email(*, tenant, order_id, payment_id):
    try:
        print(f"Attempting to send order paid email for order_id={order_id}, payment_id={payment_id}")
        send_order_paid_email(
            tenant=tenant,
            order_id=order_id,
            payment_id=payment_id,
        )
    except Exception as exc:
        print(f"Order paid email failed for order_id={order_id}, "
              f"payment_id={payment_id}: {exc}")

def send_order_paid_email(*, tenant, order_id, payment_id):
    with tenant_context(tenant):
        order = (
            Order.objects
            .select_related("subject")
            .prefetch_related("items")
            .get(id=order_id)
        )

        payment = OrderPayment.objects.get(id=payment_id)

        if payment.confirmation_email_sent:
            print(f"Confirmation email already sent for payment {payment.id}")
            return

        recipient = (order.customer_email or "").strip()
        if not recipient and order.subject_id:
            recipient = (order.subject.email or "").strip()

        if not recipient:
            print(f"Skipping confirmation email for order {order_id}: no email found")
            return
        
        print(f"Sending order confirmation email to {recipient} for order {order_id}")

        context = {
            "order": order,
            "items": order.items.all(),
            "latest_payment": payment,
            "tenant": tenant,
        }

        subject = f"Order Confirmation - {order.order_id}"
        template_name = get_order_confirmation_template(tenant=tenant)
        print(f"Using email template: {template_name}")
        html_body = render_to_string(template_name, context)
        text_body = strip_tags(html_body)
        print("JUST BEFORE SENDING EMAIL")
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")
        print("Email message constructed, attaching invoice PDF")
        pdf_bytes = build_invoice_pdf_bytes(order=order, latest_payment=payment)
        message.attach(
            f"invoice_{order.order_id}.pdf",
            pdf_bytes,
            "application/pdf",
        )
        print("Invoice PDF attached")

        message.send(fail_silently=False)

        payment.confirmation_email_sent = True
        payment.confirmation_email_sent_at = timezone.now()
        payment.save(update_fields=[
            "confirmation_email_sent",
            "confirmation_email_sent_at",
        ])
