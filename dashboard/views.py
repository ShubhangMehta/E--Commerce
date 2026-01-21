from django.shortcuts import render
#from django.contrib.auth.decorators import login_required
#from orders.models import Order
#from catalogue.models import Product
#from users.models import TenantUser

from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .services.app_registry import TENANT_APPS

#@login_required
def dashboard(request):
    apps = []
    if not request.user.is_authenticated: 
        # Replace with a tenant you want to preview
        from customers.models import Client  # or whatever your Tenant model is
        client = Client.objects.first()  # pick the first tenant for testing
    else:
        client = request.user.client
    theme = client.theme

    for app in TENANT_APPS:
        apps.append({
            'name': app['name'],
            'description': app['description'],
            'icon': app['icon'],
            'url': reverse(app['url_name']),
        })

    return render(request, 'dashboard/dashboard.html', {
        'apps': apps,
        'tenant': client,
        'theme_base': f"themes/{theme}/base_storefront.html",
    })



# Create your views here.
@login_required
def index(request):
    client = request.user.client
    theme = client.theme
    return render(request, f"themes/{theme}/index.html", {
        "tenant": client
    })


@login_required
def theme_settings(request):
    client = request.user.client

    selected_theme = request.GET.get("theme")
    if selected_theme:
        client.theme = selected_theme
        client.save()

    return render(request, "tenant_dashboard/themes.html", {
        "tenant": client
    })

