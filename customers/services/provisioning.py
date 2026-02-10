# customers/services/provisioning.py
from django.db import transaction, connection
from django.utils import timezone
from datetime import timedelta
from django_tenants.utils import schema_context, get_public_schema_name
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from customers.models import Client, Domain, ClientSubscription
from core_app.emails.utils import send_html_email
from django.conf import settings
from accounts.services import get_or_create_global_user
from users.models import SubjectMember, TenantRole

User = get_user_model()

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
                catalog_template=tenant_request.catalog_template,
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

    temp_password = get_random_string(length=12)
    username = f"{tenant_request.owner_name.split(' ')[0].lower()}_{get_random_string(3).lower()}"

    with schema_context(get_public_schema_name()):
        # Create global user (if needed) and link to tenant's SubjectMember
        user, created = get_or_create_global_user(
            first_name=tenant_request.owner_name.split()[0] if tenant_request.owner_name else "",
            last_name=" ".join(tenant_request.owner_name.split()[1:]) if tenant_request.owner_name else "",
            username=username,
            email=tenant_request.email.strip().lower(),
            password=temp_password
        )

    connection.set_schema_to_public()   # Ensure we're on public schema before running migrations for the new tenant
    call_command('migrate_schemas', schema_name=tenant.schema_name, interactive=False, verbosity=0)

    with schema_context(tenant.schema_name):    
        #create owner and admin SubjectMember
        U1= SubjectMember.objects.get_or_create(
                global_user_id=user.id, # No global user yet, will link on first login
                defaults={
                    "role": TenantRole.OWNER,
                    "full_name": tenant_request.owner_name,
                    "email": tenant_request.email,
                    "phone": None,
                    "is_active": True,
                }
            )
        
    print("U1 SubjectMember created:", U1[1], "for user:", user.email, "with role OWNER ✅")
    
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
                "email": tenant_request.email,
                "username": username,
                "subscription_type": "Trial" if subscription.is_trial else "Paid",
                "login_url": f"https://{full_domain}/login/",
                "dashboard_url": f"https://{full_domain}/dashboard/",
                "temp_password": temp_password,
                "is_trial": subscription.is_trial,
                "trial_days": settings.BILLING_TRIAL_DAYS,
            }
        )
    except Exception:
        pass
      
    print("Sent tenant created email to:", tenant_request.email, "✅")    

    return tenant, domain, subscription
