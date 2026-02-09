from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context, get_public_schema_name

def get_or_create_global_user(first_name: str, last_name: str, username: str, email: str, password: str):
    """
    Creates/Fetches global identity in public schema.
    Use email as username for simplicity.
    """
    email = email.strip().lower()
    with schema_context(get_public_schema_name()):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            username=username,
            defaults={"email": email, "first_name": first_name, "last_name": last_name},
        )
        if created:
            user.set_password(password)
            user.save()
        return user, created
    
    