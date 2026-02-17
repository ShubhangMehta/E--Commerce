from django_tenants.utils import get_public_schema_name
from django.db import connection
from .models import SubjectMember

class TenantMemberMiddleware:
    """
    Tenant schema:
    - Runs in tenant schema.
    - Attaches request.subject_member for authenticated users.
    Public schema:
    - Does nothing
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.subject_member = None

        if connection.schema_name == get_public_schema_name():
            return self.get_response(request)

        if request.user.is_authenticated:
            request.subject_member = SubjectMember.objects.filter(
                global_user_id=request.user.id,
                is_active=True
            ).first()

        return self.get_response(request)
