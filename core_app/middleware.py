from django.http import HttpResponseForbidden
from django.db import connection

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

        #if not current_schema == 'public' block it
        if current_schema != 'public' and request.path.startswith('/admin/'):
            return HttpResponseForbidden("<h2> Access Denied </h2>" 
                "<p>Access to admin site is restricted for tenant schemas.</p>"
            )
        
        return self.get_response(request)
    