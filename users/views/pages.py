from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from users.models import SubjectMember

#login_required
def users_home(request):
    users = SubjectMember.objects.all()

    # get tenant
    if not request.user.is_authenticated:
        # Replace with a tenant you want to preview
        from customers.models import Client  # or whatever your Tenant model is
        client = Client.objects.first()  # pick the first tenant for testing
    else:
        client = request.tenant
    theme = client.theme

    return render(request, "dashboard/index.html", {
        "users": users,
        "tenant": client,
        "theme_base": f"themes/{theme}/storefront.html",
    })



#def signup_view(request):
#    theme = request.tenant.theme
#
#    if request.method == "POST":
#        username = request.POST.get("username")
#        email = request.POST.get("email")
#        password = request.POST.get("password")
#
#        if User.objects.filter(username=username).exists():
#            messages.error(request, "Username already exists")
#        else:
#            user = User.objects.create_user(
#                username=username,
#                email=email,
#                password=password
#            )
#
#            CustomerUser.objects.create(
#                user=user,
#                full_name=username
#            )
#
#            login(request, user)
#            return redirect("/")
#
#    return render(request, f"themes/{theme}/signup.html")
#
#
#def login_view(request):
#    theme = request.tenant.theme
#
#    if request.method == "POST":
#        username = request.POST.get("username")
#        password = request.POST.get("password")
#
#        user = authenticate(request, username=username, password=password)
#        if user:
#            login(request, user)
#            return redirect("/")
#        else:
#            messages.error(request, "Invalid credentials")
#
#    return render(request, f"themes/{theme}/login.html")
#