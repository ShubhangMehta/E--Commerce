from django.http import HttpResponseForbidden, HttpResponse
from django.db import connection
from django.utils import timezone
from datetime import timedelta

GRACE_PERIOD_DAYS = 7  # Number of grace period days after subscription end

class BlockTenantAdminMiddleware:
    """
    Middleware to block access to the admin site for tenant schemas.
    Only the public schema should have access to the admin site.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check current schema
        current_schema = connection.schema_name
        print("Current Schema >>>> ", connection.schema_name)

        #if not current_schema == 'public' block it
        if current_schema != 'public' and request.path.startswith('/admin/'):
            return HttpResponseForbidden("<h2> Access Denied </h2>" 
                "<p>Access to Super admin site is restricted for tenant schemas.</p>"
            )
        
        return self.get_response(request)
    


class SubscriptionEnforcementMiddleware:
    """
    For tenant schemas (non-public), block the app if the tenant's subscription_end is in the past.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        schema = connection.schema_name
        print("SCHEMA:", schema)

        if schema != "public":
            from customers.models import Client
            try:
                client = Client.objects.get(schema_name=schema)
            except Client.DoesNotExist:
                return self.get_response(request)
            
            today = timezone.now().date()
            # 1 check if subscription is expired
            if client.status == 'Suspended':
                return HttpResponse(
                    "<h2> Subscription Expired </h2>"
                    "<p>Please renew your subscription to continue using the service. For any support, please contact Customer care support!</p>"
                )
            
            # 2 Check Expiry
            if client.subscription_end: # No .date needed - subscription_end is already a DateField
                expiry_date = client.subscription_end

                if hasattr(expiry_date, 'date'):
                    expiry_date = expiry_date.date()

                grace_end = expiry_date + timedelta(days=GRACE_PERIOD_DAYS)

                if today > grace_end: # Fully expired after grace period
                    return HttpResponse(
                        "<h2> Subscription Expired </h2>"
                        "<p>Your grace period has ended. Please renew to regain access. For any support, please contact Customer care support!</p>"
                        "<a href='/billing/renew/'>Renew Subscription</a>",
                        status=402
                    )
                
                elif expiry_date < today <= grace_end: # Within grace period
                    request.grace_warning = f"Your subscription expired on {expiry_date}. You have {GRACE_PERIOD_DAYS - (today - expiry_date).days} days left to renew. "

            return self.get_response(request)
        
        return self.get_response(request)
    

