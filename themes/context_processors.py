

def tenant_theme(request):
    """
    Makes the tenant's theme base templates available to any template.
    Assumes django-tenants: request.tenant exists on tenant domains.
    """
    tenant = getattr(request, "tenant", None)
    theme = getattr(tenant, "theme", None) or "default"

    return {
        "tenant": tenant,
        "tenant_theme": theme,
        "theme_storefront": f"themes/{theme}/storefront.html",
        "theme_dashboard": f"themes/{theme}/dashboard.html",
        #"tenant_logo_url": getattr(getattr(tenant, "logo", None), "url", None)   
    }