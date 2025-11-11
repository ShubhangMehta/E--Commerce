from django.http import HttpResponseForbidden
from django.db import connection
from django.http import HttpResponse
from django.utils import timezone

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
                "<p>Access to admin site is restricted for tenant schemas.</p>"
            )
        
        return self.get_response(request)
    


class SubscriptionEnforcementMiddleware:
    """
    For tenant schemas (non-public), block the app if the tenant's subscription_end is in the past.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if connection.schema_name != "public":
            from customers.models import Client
            try:
                client = Client.objects.get(schema_name=connection.schema_name)
                if client.subscription_end and client.subscription_end < timezone.now().date():
                    return HttpResponse(
                        "<h2>Subscription Expired</h2><p>Please renew to continue using the service.</p>",
                        status=402
                    )
                if client.status == "Suspended":
                    return HttpResponse("<h2>Account Suspended</h2>", status=403)
            except Client.DoesNotExist:
                pass
        return self.get_response(request)
