# customers/admin.py
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from django.utils.html import format_html
from datetime import date

from customers.models import Client, Domain, TenantRequest
from billing.models import Subscription


class SubscriptionInline(admin.TabularInline):
    model = Subscription
    extra = 0
    fields = ("plan", "status", "started_at", "current_period_start", "current_period_end", "razorpay_subscription_id", "email")
    readonly_fields = ("razorpay_subscription_id",)
    can_delete = False


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ("domain", "tenant_name_display", "is_primary", "tenant_status_display")
    list_filter = ("is_primary", "tenant__status")
    search_fields = ("domain", "tenant__tenant_name", "tenant__schema_name")

    def tenant_name_display(self, obj):
        return obj.tenant.tenant_name
    tenant_name_display.short_description = "Tenant Name"

    def tenant_status_display(self, obj):
        return obj.tenant.status
    tenant_status_display.short_description = "Status"


@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    inlines = [SubscriptionInline]

    list_display = (
        "tenant_name",
        "schema_name",
        "status",
        "plan_type",
        "subscription_end",
        "display_payment_due",
        "display_usage_summary",
        "created_on",
    )

    list_filter = ("status", "plan_type")
    search_fields = ("tenant_name", "schema_name")
    ordering = ("-created_on",)

    fieldsets = (
        ("🏢 Core Tenant Information", {
            "fields": (("tenant_name", "schema_name"), "server_name", "desired_domain", "status"),
        }),
        ("💳 Subscription & Billing", {
            "fields": (("plan_type", "subscription_end"),   # ✅ removed subscription_start here
                       ("last_payment_date", "next_due_date"), "total_orders_value"),
        }),
        ("📊 Usage & Performance Metrics", {
            "fields": (("storage_used_mb", "product_count", "order_count"),
                       ("visitor_count_7d", "visitor_count_30d", "active_users", "last_login")),
            "classes": ("collapse",),
        }),
        ("💰 Payment Processing", {
            "fields": (("payment_mode", "payment_status"),),
            "classes": ("collapse",),
        }),
    )

    actions = ["suspend_tenants", "activate_tenants"]

    def suspend_tenants(self, request, queryset):
        updated = queryset.update(status="Suspended")
        self.message_user(request, f"{updated} tenant(s) suspended.")
    suspend_tenants.short_description = "Suspend selected tenants"

    def activate_tenants(self, request, queryset):
        updated = queryset.update(status="Active")
        self.message_user(request, f"{updated} tenant(s) activated.")
    activate_tenants.short_description = "Activate selected tenants"

    def display_payment_due(self, obj):
        if getattr(obj, "next_due_date", None):
            return f"Due: {obj.next_due_date}"
        return "N/A"
    display_payment_due.short_description = "Next Due"

    def display_usage_summary(self, obj):
        product_count = getattr(obj, "product_count", None)
        order_count = getattr(obj, "order_count", None)
        storage_used = getattr(obj, "storage_used_mb", None)
        return f"P:{product_count} | O:{order_count} | S:{storage_used}MB"
    display_usage_summary.short_description = "Usage"

    # ✅ subscription_start stays readonly here
    readonly_fields = (
        "subscription_start",  # <-- FIX HERE
        "created_on", "storage_used_mb", "product_count", "order_count",
        "visitor_count_7d", "visitor_count_30d", "active_users", "last_login",
        "total_orders_value", "last_payment_date",
    )

@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
    list_display = ("tenant_name", "desired_domain", "is_approved", "requested_on")
    list_filter = ("status",)
    actions = ["approve_selected_tenants"]

    @admin.action(description="Approve selected tenants")
    def approve_selected_tenants(self, request, queryset):
        from django.db import connection
        from django_tenants.utils import schema_context
        from customers.models import Client, Domain

        try:
            connection.set_autocommit(True)
            with schema_context("public"):
                for tenant_request in queryset.filter(is_approved=False):
                    schema_name = tenant_request.tenant_name.lower().replace(" ", "_")

                    tenant_request.is_approved = True
                    tenant_request.status = "Approved"
                    tenant_request.save()

                    tenant = Client(
                        schema_name=schema_name,
                        tenant_name=tenant_request.tenant_name,
                        server_name="VPS-001",
                        desired_domain=tenant_request.desired_domain,
                        plan_type=tenant_request.plan_type,
                        payment_mode=tenant_request.payment_mode,
                        email=tenant_request.email,
                        company=tenant_request.company,
                        address=tenant_request.address,
                        logo=tenant_request.logo,
                    )
                    tenant.save()
                    tenant.create_schema(check_if_exists=True)

                    Domain.objects.create(
                        domain=f"{tenant_request.desired_domain}.localhost",
                        tenant=tenant,
                        is_primary=True,
                    )

            connection.set_autocommit(False)
            self.message_user(request, "✅ Tenants approved and schemas created successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.message_user(request, f"❌ Error approving tenants: {e}", level="error")
