# users/permissions.py
from django.http import HttpResponseForbidden


def require_roles(*roles):
    def deco(view):
        def _wrapped(request, *args, **kwargs):
            m = getattr(request, "subject_member", None)
            if not m or not m.is_active or m.role not in roles:
                return HttpResponseForbidden("Not allowed")
            return view(request, *args, **kwargs)
        return _wrapped
    return deco
