

def tenant_settings(request):

    tenant = request.tenant
    return {"tenant": tenant}

