from django.conf import settings
from django.db import connection
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string, select_template
from django.utils import timezone
from django_tenants.utils import schema_context

from orders.models import Order
from payments.models import OrderPayment
from payments.services.invoice_service import build_invoice_pdf_bytes
    
def get_order_confirmation_template():
    tenant = getattr(connection, "tenant", None)
    theme = getattr(tenant, "theme", "default") if tenant else "default"

    template = select_template([
        f"themes/{theme}/emails/order_confirmation.html",
        "emails/order_confirmation.html",
    ])
    return template.template.name


def safe_send_order_paid_email(*, tenant, order_id, payment_id):
    try:
        send_order_paid_email(
            tenant=tenant,
            order_id=order_id,
            payment_id=payment_id,
        )
    except Exception as exc:
        print(f"Order paid email failed for order_id={order_id}, "
              f"payment_id={payment_id}: {exc}")

def send_order_paid_email(*, tenant, order_id, payment_id):
    with schema_context(tenant):
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

        context = {
            "order": order,
            "items": order.items.all(),
            "latest_payment": payment,
            "tenant": tenant,
        }

        subject = f"Order Confirmation - {order_id}"
        template_name = get_order_confirmation_template()
        html_body = render_to_string(template_name, context)
        text_body = strip_tags(html_body)

        message = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[recipient],
        )
        message.attach_alternative(html_body, "text/html")

        pdf_bytes = build_invoice_pdf_bytes(order=order, latest_payment=payment)
        message.attach(
            f"invoice_{order_id}.pdf",
            pdf_bytes,
            "application/pdf",
        )

        message.send(fail_silently=False)

        payment.confirmation_email_sent = True
        payment.confirmation_email_sent_at = timezone.now()
        payment.save(update_fields=[
            "confirmation_email_sent",
            "confirmation_email_sent_at",
        ])

# def render_order_paid_email(*, tenant, context):
#     html_tpl = select_template([
#         f"themes/{tenant.theme}/emails/order_paid.html",
#         "themes/default/emails/order_paid.html",
#     ])
#     text_tpl = select_template([
#         f"themes/{tenant.theme}/emails/order_paid.txt",
#         "themes/default/emails/order_paid.txt",
#     ])
#     print(f"Selected HTML template for tenant '{tenant.schema_name}': {html_tpl.template.name}")
#     print(f"Selected Text template for tenant '{tenant.schema_name}': {text_tpl.template.name}")
#     return html_tpl.render(context), text_tpl.render(context)