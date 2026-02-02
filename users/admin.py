from django.contrib import admin
from django.db import connection
from django.http import HttpResponse
from django.contrib.auth.models import User

from .models import SubjectMember, Coordinate


class TenantOnlyAdmin(admin.ModelAdmin):
    def has_module_permission(self, request):
        # Hide from sidebar in PUBLIC schema
        return connection.schema_name != "public"

    def has_view_permission(self, request, obj=None):
        return connection.schema_name != "public"

    def changelist_view(self, request, extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse(
                "<h2 style='padding: 40px;'>Not available for global schema</h2>"
            )
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url="", extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse(
                "<h2 style='padding: 40px;'>Not available for global schema</h2>"
            )
        return super().change_view(request, object_id, form_url, extra_context)

    def add_view(self, request, form_url="", extra_context=None):
        if connection.schema_name == "public":
            return HttpResponse(
                "<h2 style='padding: 40px;'>Not available for global schema</h2>"
            )
        return super().add_view(request, form_url, extra_context)


@admin.register(SubjectMember)
class SubjectMemberAdmin(TenantOnlyAdmin):
    list_display = (
        "id",
        "email",
        "full_name",
        "role",
        "phone",
        "is_active",
    )

    search_fields = (
        "email",
        "full_name",
        "phone",
    )

    list_filter = ("role", "is_active")
    ordering = ("id",)

@admin.register(Coordinate)
class CoordinateAdmin(TenantOnlyAdmin):
    list_display = (
        "id",
        "subject_email",
        "house_no",
        "landmark",
        "city",
        "state",
        "postal_code",
        "address_type",
        "is_default",
    )

    search_fields = (
        "user__email",
        "house_no",
        "city",
        "state",
        "postal_code",
    )

    list_filter = ("city", "state", "address_type", "is_default")
    ordering = ("id",)

    def subject_email(self, obj):
        return obj.user.email

    subject_email.short_description = "Email"
