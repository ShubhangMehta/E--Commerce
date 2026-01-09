# customers/services/provisioning.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django_tenants.utils import schema_context
from django.core.management import call_command

from customers.models import Client, Domain, ClientSubscription
from core_app.emails.utils import send_html_email
from django.conf import settings

def provision_tenant_from_request(*, tenant_request, plan, pricing):
    """
    Creates:
    - Client (tenant)
    - Domain
    - Schema migrations (if needed)
    - ClientSubscription (trial or paid)
    Returns: (tenant, domain, subscription)
    """
    base_domain = tenant_request.desired_domain
    if not base_domain.endswith(settings.BILLING_DOMAIN_SUFFIX):
        full_domain = f"{base_domain}{settings.BILLING_DOMAIN_SUFFIX}"
    else:
        full_domain = base_domain

    # Safety checks
    if Domain.objects.filter(domain=full_domain).exists():
        raise ValueError(f"Domain already exists: {full_domain}")

    with transaction.atomic():
            schema_name = full_domain.split('.')[0].replace('-', '_')

            tenant = Client.objects.create(
                owner_name=tenant_request.owner_name,
                tenant_name=tenant_request.tenant_name,
                schema_name=schema_name,
                desired_domain=full_domain,
                email=tenant_request.email,
                company=tenant_request.company,
                theme=tenant_request.theme,
            )

            domain = Domain.objects.create(
                domain=full_domain,
                tenant=tenant,
                is_primary=True
            )

            if pricing.billing_cycle == "trial":
                subscription = ClientSubscription.objects.create(
                    client=tenant,
                    plan=plan,
                    pricing=pricing,
                    start_date=timezone.now(),
                    end_date=timezone.now() + timedelta(days=settings.BILLING_TRIAL_DAYS),
                    status='active'
                )
                tenant.used_trial = True
                tenant.save(update_fields=['used_trial'])
            else:
                subscription = ClientSubscription.objects.create(
                    client=tenant,
                    plan=plan,
                    pricing=pricing,
                    status='active'
                )

    try:
        send_html_email(
            subject="Your Store Is Ready",
            to_email=tenant_request.email,
            template_name="emails/tenant_created.html",
            context={
                "owner_name": tenant_request.tenant_name,
                "tenant_name": tenant.tenant_name,
                "company": tenant_request.company,
                "domain": full_domain,
                "plan": plan.name,
                "subscription_type": "Trial" if subscription.is_trial else "Paid",
                "login_url": f"https://{full_domain}/login/",
                "dashboard_url": f"https://{full_domain}/dashboard/",
                "is_trial": subscription.is_trial,
                "trial_days": settings.BILLING_TRIAL_DAYS,
            }
        )
    except Exception:
        pass
      
    print("Sent tenant created email to:", tenant_request.email, "✅")    

    # 4) (Optional) Run tenant migrations explicitly if your setup requires it
    # Some projects rely on auto_create_schema=True, others run migrations manually.
    # Only enable if you need it.
    #
    with schema_context(tenant.schema_name):
        call_command('migrate', interactive=False, verbosity=0)

    return tenant, domain, subscription
