from django.http import Http404
from functools import wraps

def single_product_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        if not tenant or tenant.product_mode != "single":
            raise Http404()
        return view_func(request, *args, **kwargs)
    return wrapper


def multi_product_only(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        tenant = getattr(request, "tenant", None)
        if not tenant or tenant.product_mode != "multi":
            raise Http404()
        return view_func(request, *args, **kwargs)
    return wrapper
