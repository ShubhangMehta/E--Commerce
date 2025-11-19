from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from datetime import date
from .models import TenantRequest, Domain
from core_app.emails.utils import send_html_email

def create_tenant(request):
    if request.method == 'POST':
        tenant_name = request.POST.get('tenant_name')
        domain_name = request.POST.get('domain_name')
        plan_type = request.POST.get('plan_type')
        payment_mode = request.POST.get('payment_mode')
        payment_plan=request.POST.get('payment_plan')
        email=request.POST.get('email')
        company=request.POST.get('company')
        address=request.POST.get('address')


        if not tenant_name or not domain_name:
            return JsonResponse({'error': 'Tenant name and Domain name are required!'}, status=400)

        # Prevent duplicate domains
        if Domain.objects.filter(domain=f"{domain_name}.localhost").exists() or TenantRequest.objects.filter(desired_domain=domain_name).exists():
            return JsonResponse({'error': 'This domain name is already taken!'}, status=400)

        # Store tenant request (pending approval)
        TenantRequest.objects.create(
            tenant_name=tenant_name,
            desired_domain=domain_name,
            plan_type=plan_type,
            payment_mode=payment_mode,
            payment_plan=payment_plan,
            email=email,
            company=company,
            address=address
        )

        send_html_email(
            subject="Your Tenant Request Has Been Received",
            to_email=email,
            template_name="emails/welcome.html",
            context={
                "name": tenant_name,
                "tenant_name": tenant_name,
                "domain": domain_name,
                "company": company,
                "email": email,
                "plan": plan_type,
            }
        )

        return JsonResponse({'message': f'Tenant request for "{tenant_name}" submitted successfully! Awaiting admin approval.'})

    return render(request, 'create_tenant.html')


def index(request):
    return HttpResponse("<h1> Public Index </h1>")
