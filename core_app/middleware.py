from django.http import HttpResponseForbidden, HttpResponse
from django.db import connection
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from django_tenants.utils import schema_context, get_public_schema_name

GRACE_PERIOD_DAYS = 7  # Number of grace period days after subscription end

class BlockTenantAdminMiddleware:
    """
    Block access to the SUPER ADMIN site for tenant schemas.
    Allow tenant admin access during development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        schema = connection.schema_name

        # Allow everything in development
        if settings.DEBUG:
            return self.get_response(request)

        # Block tenant admin in production
        if schema != "public" and request.path.startswith("/admin/"):
            return HttpResponseForbidden(
                "<h2>Access Denied</h2>"
                "<p>Tenant admin access is restricted.</p>"
            )

        return self.get_response(request)

