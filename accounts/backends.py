from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context, get_public_schema_name

class PublicSchemaModelBackend(ModelBackend):
    """
    Forces authentication + user lookup to use the public schema only.
    so identities are global (single user table for all tenants).
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        public_schema = get_public_schema_name()

        with schema_context(public_schema):
            UserModel = get_user_model()

            # Supports both username and email authentication
            # Here we try usernmame first, then email fallback
            user = None
            if username:
                try:
                    user = UserModel.objects.get(username=username)
                except UserModel.DoesNotExist:
                    # Email fallback
                    try:
                        user = UserModel.objects.get(email__iexact=username)
                    except UserModel.DoesNotExist:
                        return None
                    
            if user and user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
        
    def get_user(self, user_id):
        public_schema = get_public_schema_name()

        with schema_context(public_schema):
            UserModel = get_user_model()
            try:
                return UserModel.objects.get(pk=user_id)
            except UserModel.DoesNotExist:
                return None
    