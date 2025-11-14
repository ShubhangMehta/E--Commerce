from django.contrib import admin
from django.contrib.admin.sites import AdminSite

admin.site.site_header = "SaaS E-commerce Super-Admin"
admin.site.site_title = "Admin Portal"
admin.site.index_title = "Welcome to the SaaS E-commerce Admin Portal"

class CustomAdminSite(AdminSite):
    site_header = "SaaS E-commerce Super-Admin"
    site_title = "Admin Portal"
    index_title = "Welcome to the SaaS E-commerce Admin Portal"

    def each_context(self, request):
        context = super().each_context(request)
        context['custom_css'] = '/static/core_app/css/custom_admin.css'
        return context
    
admin_site = CustomAdminSite()
