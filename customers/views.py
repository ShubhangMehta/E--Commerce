from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from .models import TenantRequest, Domain, SubscriptionPlan, Ticket, Client 
from core_app.emails.utils import send_html_email
from django.contrib import messages
from .rzp_services import create_subscription_checkout
from django.db import connection
from django.conf import settings


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



def create_tenant(request):
    if request.method == 'POST':
        tenant_name = request.POST.get('tenant_name')
        domain_name = request.POST.get('domain_name')
        plan_name = request.POST.get('plan')  # basic / standard / premium
        subscription_type = request.POST.get('subscription_type')  # trial / paid
        payment_plan = request.POST.get('payment_plan')  # monthly / yearly (only if paid)
        theme = request.POST.get('theme')  # default / minimal / modern

        email = request.POST.get('email')
        company = request.POST.get('company')
        address = request.POST.get('address')
        logo = request.FILES.get('logo')

        if not tenant_name or not domain_name or not plan_name:
            return JsonResponse(
                {'error': 'Tenant name, domain name, and plan are required'},
                status=400
            )

        # Prevent duplicate domains
        full_domain = f"{domain_name}.localhost"
        if (
            Domain.objects.filter(domain=full_domain).exists() or
            TenantRequest.objects.filter(desired_domain=domain_name).exists()
        ):
            return JsonResponse(
                {'error': 'This domain is already taken.'},
                status=400
            )

        # Fetch subscription plan by name
        plan = SubscriptionPlan.objects.filter(name__iexact=plan_name).first()
        if not plan:
            return JsonResponse(
                {'error': 'Invalid plan selected.'},
                status=400
            )

        # Trial vs Paid handling
        is_trial = subscription_type == 'trial'

        if is_trial:
            payment_plan = None  # no billing cycle for trial

        # Store tenant request
        TenantRequest.objects.create(
            tenant_name=tenant_name,
            desired_domain=domain_name,
            plan=plan,
            payment_plan=payment_plan,
            theme=theme,
            email=email,
            company=company,
            address=address,
            logo=logo
        )

        # Send confirmation email
        send_html_email(
            subject="Your Tenant Request Has Been Received",
            to_email=email,
            template_name="emails/welcome.html",
            context={
                "name": tenant_name,
                "tenant_name": tenant_name,
                "domain": domain_name,
                "company": company,
                "plan": plan.name,
                
            }
        )

        return JsonResponse(
            {'message': f'Request for {tenant_name} submitted for approval!'}
        )

    return render(request, 'create_tenant.html')



def home(request):
    return HttpResponse("<h1> Public Index </h1>")


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
