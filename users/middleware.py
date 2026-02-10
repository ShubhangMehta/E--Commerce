from django_tenants.utils import get_public_schema_name
from django.db import connection
from .models import SubjectMember, TenantRole

class TenantMemberMiddleware:
    """
    Tenant schema:
    - Runs in tenant schema.
    - Attaches request.subject_member for authenticated users.
    - If missing, auto creates a minimal SubjectMember as CUSTOMER
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
            member = SubjectMember.objects.filter(
                global_user_id=request.user.id,
                is_active=True
            ).first()

            if member is None:
                member = SubjectMember.objects.create(
                    global_user_id=request.user.id,
                    role=TenantRole.CUSTOMER,
                    full_name=(getattr(request.user, "get_full_name", lambda: "")() or request.user.username()),
                    email=(getattr(request.user, "email", "") or request.user.get_username()),
                    phone=None,
                    is_active=True,
                )

            request.subject_member = member

        return self.get_response(request)
