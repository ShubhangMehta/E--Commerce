from decimal import Decimal
import email
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from django.contrib import messages
from django.db import connection

from .models import Client, Domain, SubscriptionPlan, TenantRequest, Ticket, PlanPricing, Invoice
from .rzp_services import get_or_create_order_for_invoice #create_subscription_checkout
from .services.provisioning import provision_tenant_from_request
from core_app.emails.utils import send_html_email

def home(request):
    return HttpResponse("<h1> E-Cartel Public Schema </h1>")


def billing_plans(request):
    """
    Show available subscription plans to tenant.
    """
    schema = connection.schema_name

    if schema == "public":
        return HttpResponse(
            "Plans must be viewed from tenant website.",
            status=400
        )

    plans = SubscriptionPlan.objects.filter(status="active").order_by("price")

    return render(
        request,
        "customers/plans.html",
        {"plans": plans}
    )


def billing_renew(request):
    schema = connection.schema_name

    if schema == 'public':
        return HttpResponse("Billing renewal is not available on the public schema.", status=400)

    try:
        client = Client.objects.get(schema_name=schema)
    except Client.DoesNotExist:
        return HttpResponse("Client not found.", status=404)
    
    plan_id = request.GET.get("plan")

    if plan_id:
        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, status='active')
        except SubscriptionPlan.DoesNotExist:
            return HttpResponse("Invalid subscription plan.", status=404)
    else:
        plan = SubscriptionPlan.objects.filter(status='active').first()
        if not plan:
            return HttpResponse("No active subscription plans available.", status=500)
    
    result = create_subscription_checkout(client, plan)

    context = {
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order": result["razorpay_order"],
        "client": client,
        "plan": plan,
        "amount": int(result["razorpay_order"]["amount"]),
    }

    return render(request, "customers/billing.html", context)


def billing_success(request):
    return render(request, "customers/billing_success.html")


def billing_cancel(request):
    return render(request, "customers/billing_cancel.html")


def _to_full_domain(domain_name: str) -> str:
    # Your current local setup
    return domain_name.strip().lower() #f"{domain_name}.localhost"

def _find_pricing(plan: SubscriptionPlan, subscription_type: str, payment_plan: str | None):
    """
    Map; form inputs to PlanPricing.billing_cycle
    - trial -> 'trial'
    - paid monthly -> 'monthly'
    - paid yearly -> 'yearly'
    """
    if subscription_type == "trial":
        billing_cycle = "trial"
    else:
        billing_cycle = (payment_plan or "monthly").lower()
    return PlanPricing.objects.filter(plan=plan, billing_cycle=billing_cycle).first()


@transaction.atomic
def create_tenant(request):
    if request.method == "GET":
        return render(request, "customers/create_tenant.html")

    # POST
    data = {
        "owner_name": request.POST.get("owner_name"),
        "tenant_name": request.POST.get("tenant_name"),
        "domain_name": request.POST.get("domain_name"),
        "plan_name": request.POST.get("plan"),
        "subscription_type": request.POST.get("subscription_type"),  # trial / paid
        "payment_plan": request.POST.get("payment_plan"),            # monthly / yearly
        "theme": request.POST.get("theme"),
        "email": request.POST.get("email"),
        "company": request.POST.get("company"),
        "address": request.POST.get("address"),
        "logo": request.FILES.get("logo"),
    }


    if not data["tenant_name"] or not data["domain_name"] or not data["plan_name"]:
        return JsonResponse(
            {"error": "Tenant name, domain name, and plan are required"},
            status=400,
        )

    full_domain = _to_full_domain(data["domain_name"])

    # If tenant already exists with this domain, block
    if Domain.objects.filter(domain=full_domain).exists():
        return JsonResponse({"error": "This domain is already taken."}, status=400)

    plan = SubscriptionPlan.objects.filter(name__iexact=data["plan_name"]).first()
    if not plan:
        return JsonResponse({"error": "Invalid plan selected."}, status=400)

    if data["subscription_type"] == "trial":
        if Client.objects.filter(email=data["email"], used_trial=True).exists():
            return JsonResponse(
                {"error": "Trial has already been used. Please choose a paid plan."},
                status=400
            )
    
    pricing = _find_pricing(
        plan=plan,
        subscription_type=data["subscription_type"],
        payment_plan=data["payment_plan"],
    )

    if not pricing:
        return JsonResponse(
            {"error": "Pricing not configured for this plan/billing cycle."},
            status=400,
        )

    # ------------------------------------------------------------------
    # RESERVE / REUSE TenantRequest (refresh-safe)
    # ------------------------------------------------------------------
    tr = TenantRequest.objects.filter(desired_domain=full_domain).order_by("-id").first()

    if tr and tr.status == "approved":
        # Already provisioned — redirect to tenant domain
        return redirect(f"http://{full_domain}:8000/")

    if not tr:
        tr = TenantRequest.objects.create(
            tenant_name=data["tenant_name"],
            desired_domain=full_domain,
            plan=plan,
            pricing=pricing,
            theme=data["theme"],
            email=data["email"],
            company=data["company"],
            address=data["address"],
            logo=data["logo"],
            status="pending",
        )
    else:
        tr.tenant_name = data["tenant_name"]
        tr.plan = plan
        tr.pricing = pricing
        tr.theme = data["theme"]
        tr.email = data["email"]
        tr.company = data["company"]
        tr.address = data["address"]
        if data["logo"]:
            tr.logo = data["logo"]
        tr.status = "pending"
        tr.save()

    # ------------------------------------------------------------------
    # TRIAL: provision immediately
    # ------------------------------------------------------------------

    if pricing.billing_cycle == "trial":
        tenant, domain, subscription = provision_tenant_from_request(
            tenant_request=tr, plan=plan, pricing=pricing
        )
        tr.status = "approved"
        tr.save(update_fields=["status"])
        return redirect(f"http://{domain.domain}:8000/")

    # ------------------------------------------------------------------
    # PAID: reuse same invoice + same order (resume behavior)
    # ------------------------------------------------------------------
    # Reuse existing unpaid invoice for this request if it exists:
    invoice = Invoice.objects.filter(tenant_request=tr).order_by("-id").first()
    if not invoice:
        # amount: pricing.price is in INR decimal -> convert to paise int
        amount_paise = int(Decimal(pricing.price))
        invoice = Invoice.objects.create(
            tenant_request=tr,
            invoice_number=f"INV-{tr.id}",
            invoice_type="auto",
            status="issued",
            amount=amount_paise,
            currency="INR",
        )

    order = get_or_create_order_for_invoice(invoice)

    # Render the SAME template, but in payment mode
    context = {
        "show_payment": True,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "order_id": order["id"],
        "amount": invoice.amount,
        "tenant_request": tr,
        "plan": plan,
        "invoice": invoice,
        "message": "Complete the payment to finish setting up your store.",
    }
    return render(request, "customers/create_tenant.html", context)


# def create_tenant(request):
#     if request.method == 'POST':
#         tenant_name = request.POST.get('tenant_name')
#         domain_name = request.POST.get('domain_name')
#         plan_name = request.POST.get('plan')  # basic / standard / premium
#         subscription_type = request.POST.get('subscription_type')  # trial / paid
#         payment_plan = request.POST.get('payment_plan')  # monthly / yearly (only if paid)
#         theme = request.POST.get('theme')  # default / minimal / modern

#         email = request.POST.get('email')
#         company = request.POST.get('company')
#         address = request.POST.get('address')
#         logo = request.FILES.get('logo')

#         if not tenant_name or not domain_name or not plan_name:
#             return JsonResponse(
#                 {'error': 'Tenant name, domain name, and plan are required'},
#                 status=400
#             )

#         # Prevent duplicate domains
#         full_domain = f"{domain_name}.localhost"
#         if (
#             Domain.objects.filter(domain=full_domain).exists() or
#             TenantRequest.objects.filter(desired_domain=domain_name).exists()
#         ):
#             return JsonResponse(
#                 {'error': 'This domain is already taken.'},
#                 status=400
#             )

#         # Fetch subscription plan by name
#         plan = SubscriptionPlan.objects.filter(name__iexact=plan_name).first()
#         if not plan:
#             return JsonResponse(
#                 {'error': 'Invalid plan selected.'},
#                 status=400
#             )

#         # Trial vs Paid handling
#         is_trial = subscription_type == 'trial'

#         if is_trial:
#             payment_plan = None  # no billing cycle for trial

#         # Store tenant request
#         TenantRequest.objects.create(
#             tenant_name=tenant_name,
#             desired_domain=domain_name,
#             plan=plan,
#             payment_plan=payment_plan,
#             theme=theme,
#             email=email,
#             company=company,
#             address=address,
#             logo=logo
#         )

#         # Send confirmation email
#         send_html_email(
#             subject="Your Tenant Request Has Been Received",
#             to_email=email,
#             template_name="emails/welcome.html",
#             context={
#                 "name": tenant_name,
#                 "tenant_name": tenant_name,
#                 "domain": domain_name,
#                 "company": company,
#                 "plan": plan.name,
#                 "is_trial": is_trial,
#             }
#         )

#         return JsonResponse(
#             {'message': f'Request for {tenant_name} submitted for approval!'}
#         )

#     return render(request, 'customers/create_tenant.html')

def raise_ticket(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        category = request.POST.get('category')

        if subject and description and category:
            Ticket.objects.create(
                client=request.tenant,
                subject=subject,
                description=description,
                category=category
            )
            messages.success(request, "Your support ticket has been submitted successfully!")
            return redirect('raise_ticket')
        else:
            messages.error(request, "Please fill all fields before submitting.")

    return render(request, 'customers/raise_ticket.html')
