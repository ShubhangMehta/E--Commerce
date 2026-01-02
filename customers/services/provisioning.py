# customers/services/provisioning.py
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django_tenants.utils import schema_context
from django.core.management import call_command

from customers.models import Client, Domain, ClientSubscription

def provision_tenant_from_request(*, tenant_request, plan, pricing):
    """
    Creates:
    - Client (tenant)
    - Domain
    - Schema migrations (if needed)
    - ClientSubscription (trial or paid)
    Returns: (tenant, domain, subscription)
    """

    # Safety checks
    if Domain.objects.filter(domain=tenant_request.desired_domain).exists():
        raise ValueError(f"Domain already exists: {tenant_request.desired_domain}")

    with transaction.atomic():
        # 1) Create tenant (Client)
        tenant = Client.objects.create(
            tenant_name=getattr(tenant_request, 'tenant_name', tenant_request.desired_domain.split('.')[0]),
            schema_name=tenant_request.desired_domain.split('.')[0].replace('-', '_'),
            desired_domain=tenant_request.desired_domain,
            email=getattr(tenant_request, 'email', None),
            company=getattr(tenant_request, 'company', None),
        )

        # 2) Create primary domain
        domain = Domain.objects.create(
            domain=tenant_request.desired_domain,
            tenant=tenant,
            is_primary=True
        )

        # 3) Create subscription (trial or paid)
        # For paid subscriptions, start as expired until captured payment exists (webhook will activate)
        if pricing and pricing.billing_cycle == 'trial':
            subscription = ClientSubscription.objects.create(
                client=tenant,
                plan=plan,
                pricing=pricing,
                start_date=timezone.now(),
                end_date=timezone.now() + timedelta(days=7),
                status='active'
            )
        else:
            subscription = ClientSubscription.objects.create(
                client=tenant,
                plan=plan,
                pricing=pricing,
                status='expired'  # webhook capture will activate
            )
        

    # 4) (Optional) Run tenant migrations explicitly if your setup requires it
    # Some projects rely on auto_create_schema=True, others run migrations manually.
    # Only enable if you need it.
    #
    # with schema_context(tenant.schema_name):
    #     call_command('migrate', interactive=False, verbosity=0)

    return tenant, domain, subscription
