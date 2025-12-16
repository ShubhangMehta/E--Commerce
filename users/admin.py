from django.contrib import admin
from django.db import connection
from django.http import HttpResponse
from .models import CustomerUser, CustomerAddress


class TenantOnlyAdmin(admin.ModelAdmin):

    def has_module_permission(self, request):
        # Hide from sidebar in PUBLIC schema
        if connection.schema_name == "public":
            return False
        return True

    def has_view_permission(self, request, obj=None):
        if connection.schema_name == "public":
            return False
        return True

    def changelist_view(self, request, extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse("<h2 style='padding: 40px;'>Not available for global schema</h2>")
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse("<h2 style='padding: 40px;'>Not available for global schema</h2>")
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse("<h2 style='padding: 40px;'>Not available for global schema</h2>")
        return super().add_view(request, form_url, extra_context)

@admin.register(CustomerUser)
class CustomerUserAdmin(TenantOnlyAdmin):
    list_display = ("id", "email", "full_name", "is_active")
    search_fields = ("email", "full_name")
    list_filter = ("is_active",)
    ordering = ("id",)


@admin.register(CustomerAddress)
class CustomerAddressAdmin(TenantOnlyAdmin):
    list_display = ("id", "user", "house_no", "landmark", "city", "state", "postal_code")
    search_fields = ("user__email", "house_no", "city", "state", "postal_code")
    list_filter = ("city", "state")
    ordering = ("id",)
