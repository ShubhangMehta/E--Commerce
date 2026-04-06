from io import BytesIO

from django.template.loader import get_template
from xhtml2pdf import pisa

from payments.models import OrderPayment

def _invoice_template_name(tenant):
    theme = getattr(tenant, "theme", "default") if tenant else "default"
    return f"themes/{theme}/cust_invoice.html"


def build_invoice_pdf_bytes(*, order, tenant=None, latest_payment=None): 
    """
    This function is used to build the invoice PDF bytes for a given order. 
    Its used in two places:
    1. When the customer views the invoice PDF from the storefront.
    2. When the customer receives the order confirmation email with the invoice PDF attached.
    The function takes an optional tenant parameter to ensure that the correct themed template is used for both the storefront(view order pdf) and email contexts.
    """
    if latest_payment is None:
        latest_payment = (
            OrderPayment.objects
            .filter(order=order)
            .order_by("-id")
            .first()
        )

    template = get_template(_invoice_template_name(tenant))
    context = {
        "order": order,
        "items": order.items.all(),
        "latest_payment": latest_payment,
        "tenant": tenant,
    }

    html = template.render(context)
    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    # if request:   #leave it for future purposes
    #     invoice_html = template.render(context, request=request)
    #     result = BytesIO()
    #     pdf = pisa.CreatePDF(invoice_html, dest=result)
    # else:
    #     email_html = template.render(context)
    #     result = BytesIO()
    #     pdf = pisa.CreatePDF(email_html, dest=result)

    if pdf.err:
        raise ValueError("Error generating PDF")

    return result.getvalue()