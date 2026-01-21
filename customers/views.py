from decimal import Decimal
from django.conf import settings
from django.shortcuts import redirect, render
from django.http import JsonResponse
from django.db import transaction
from django.contrib import messages
from django.views.decorators.http import require_GET


from .models import Client, Domain, SubscriptionPlan, TenantRequest, Ticket, PlanPricing, Invoice
from .rzp_services import get_or_create_order_for_invoice
from .services.provisioning import provision_tenant_from_request


def home(request):
    context = {
        "page_title": "E-Cartel",
        "hero_title": "Launch your online store in minutes",
        "hero_subtitle": "A multi-tenant e-commerce platform with subscriptions, themes, and scalable infrastructure.",
        "cta_primary": "Start Free Trial",
        "cta_secondary": "View Plans",
    }
    return render(request, "customers/home.html", context)
    #return HttpResponse("<h1> E-Cartel Public Schema </h1>")

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
        "owner_name": request.POST.get("owner_name").strip().lower(),
        "tenant_name": request.POST.get("tenant_name").strip().lower(),
        "domain_name": request.POST.get("domain_name").strip().lower(),
        "plan_name": request.POST.get("plan"),
        "subscription_type": request.POST.get("subscription_type"),  # trial / paid
        "payment_plan": request.POST.get("payment_plan"),            # monthly / yearly
        "theme": request.POST.get("theme"),
        "email": request.POST.get("email").strip().lower(),
        "company": request.POST.get("company").strip().lower(),
        "address": request.POST.get("address").strip().lower(),
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
            owner_name=data["owner_name"],
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
        tr.owner_name = data["owner_name"]
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
        return redirect(f"http://{domain.domain}:8000/") #Redirecting to index page of domain/website

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


@require_GET
def billing_success(request):
    invoice_id = request.GET.get("invoice_id") or request.GET.get("invoice")
    if not invoice_id:
        return JsonResponse({"error": "Missing invoice_id/invoice", "received_query_params": dict(request.GET)}, status=400)

    invoice = Invoice.objects.filter(id=invoice_id).select_related("client").first()
    if not invoice:
        return JsonResponse({"error": "Invoice not found", "invoice_id": invoice_id}, status=404)

    # Make status check case-tolerant (in case your choices store "Paid")
    if (invoice.status or "").lower() == "paid" and invoice.client_id:
        # Try primary first, then fallback to any domain
        primary_domain = Domain.objects.filter(tenant_id=invoice.client_id, is_primary=True).first()
        if not primary_domain:
            primary_domain = Domain.objects.filter(tenant_id=invoice.client_id).order_by("-is_primary", "id").first()

        if primary_domain:
            scheme = "https" if request.is_secure() else "http"

            # DEV: if you’re running tenants on :8000, include it
            return redirect(f"{scheme}://{primary_domain.domain}:8000/")

        # If paid but no domain, show debug on page (temporary)
        return JsonResponse({
            "error": "Invoice paid but no domain found",
            "invoice_id": invoice.id,
            "client_id": invoice.client_id,
            "domains": list(Domain.objects.filter(tenant_id=invoice.client_id).values("domain", "is_primary")),
        }, status=500)

    return render(request, "customers/billing_success.html", {"invoice_id": invoice_id})

@require_GET
def billing_cancel(request):
    return render(request, "customers/billing_cancel.html")


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
