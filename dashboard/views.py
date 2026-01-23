from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.exceptions import PermissionDenied

# Create your views here.
@login_required
def dashboard(request):
    """
    Render dashboard page.
    """
    context = {}
    # if not request.user.is_staff:
    #     raise PermissionDenied
    return render(request, "dashboard/dashboard.html", context)
