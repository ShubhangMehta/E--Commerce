from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from ..models import CustomerUser

#@login_required
def users_home(request):
    users = CustomerUser.objects.all()
    return render(request, "index.html", {
        "users": users
    })
