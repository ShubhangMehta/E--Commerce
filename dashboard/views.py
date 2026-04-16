from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .services.app_registry import TENANT_APPS
from catalog.models import SingleProduct
from orders.models import Order
from users.models import SubjectMember  # if you created this app


#@login_required
def dashboard(request):
    apps = []
    if not request.user.is_authenticated: 
        # Replace with a tenant you want to preview
        from customers.models import Client  # or whatever your Tenant model is
        client = Client.objects.first()  # pick the first tenant for testing
    else:
        client = request.tenant
    theme = client.theme
    product_count = SingleProduct.objects.count()
    order_count = Order.objects.filter(tenant=client).count()

    # if visitor tracking exists
    visitor_count = SubjectMember.objects.count()

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
        'theme_base': f"themes/{theme}/storefront.html",
        "product_count": product_count,
        "order_count": order_count,
        "visitor_count": visitor_count,
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

    return render(request, "dashboard.html", {
        "tenant": client
    })

