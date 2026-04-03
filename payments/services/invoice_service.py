from io import BytesIO
from urllib import request

from django.db import connection
from django.template.loader import get_template
from httpx import request
from xhtml2pdf import pisa

from payments.models import OrderPayment

def _invoice_template_name():
    tenant = getattr(connection, "tenant", None)
    theme = getattr(tenant, "theme", "default") if tenant else "default"
    return f"themes/{theme}/cust_invoice.html"


def build_invoice_pdf_bytes(*, order, request=None, latest_payment=None):
    if latest_payment is None:
        latest_payment = (
            OrderPayment.objects
            .filter(order=order)
            .order_by("-id")
            .first()
        )

    template = get_template(_invoice_template_name())
    context = {
        "order": order,
        "items": order.items.all(),
        "latest_payment": latest_payment,
        "tenant": getattr(connection, "tenant", None),
    }

    # ✅ Pass request so {{ request }} works in template
    html = template.render(context, request=request)

    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        raise ValueError("Error generating PDF")

    return result.getvalue()