from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from users.models import SubjectMember

#login_required
# def users_home(request):
#     users = SubjectMember.objects.all()

#     # get tenant
#     if not request.user.is_authenticated:
#         # Replace with a tenant you want to preview
#         from customers.models import Client  # or whatever your Tenant model is
#         client = Client.objects.first()  # pick the first tenant for testing
#     else:
#         client = request.tenant
#     theme = client.theme

#     return render(request, "dashboard/index.html", {
#         "users": users,
#         "tenant": client,
#         "theme_base": f"themes/{theme}/storefront.html",
#     })

