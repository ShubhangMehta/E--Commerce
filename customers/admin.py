from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from django.db import connection
from django_tenants.utils import schema_context
from .models import (
    Client, Domain, TenantRequest, SubscriptionPlan,
    Ticket, ClientSubscription, Payment, Invoice, RefundRequest
)


# ----------------------------
# Domain Admin
# ----------------------------
@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant_name_display', 'is_primary', 'tenant_status_display')
    list_filter = ('is_primary',)
    search_fields = ('desired_domain', 'tenant__tenant_name', 'tenant__schema_name')

    def tenant_name_display(self, obj):
        return obj.tenant.tenant_name
    tenant_name_display.short_description = 'Tenant Name'
    
    def tenant_status_display(self, obj):
        return obj.tenant.status
    tenant_status_display.short_description = 'Status'


# ----------------------------
# Client Admin
# ----------------------------
@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    list_display = (
        'tenant_name',
        'schema_name',
        'status',           # from @property
        'current_plan',     # from @property
        'subscription_start',
        'subscription_end',
        'created_on',
        )
    readonly_fields = (
    'created_on',
    'status',
    'current_plan',
    'subscription_start',
    'subscription_end',
    'storage_used_mb',
    'product_count',
    'order_count',
    'visitor_count_7d',
    'visitor_count_30d',
    'active_users',
    'last_login',
)
    list_filter = ('desired_domain',)
    search_fields = ('tenant_name', 'schema_name')
    ordering = ('-created_on',)

    fieldsets = (
        ('🏢 Core Tenant Information', {
            'fields': (('tenant_name', 'schema_name'), 'server_name', 'desired_domain', 'status'),
        }),
        ('💳 Subscription & Billing', {
            'fields': (('current_plan', 'subscription_end'), 'subscription_start'),
        }),
        ('📊 Usage & Performance Metrics', {
            'fields': (
                ('storage_used_mb', 'product_count', 'order_count'),
                ('visitor_count_7d', 'visitor_count_30d', 'active_users', 'last_login')
            ),
            'classes': ('collapse',),
        }),
    )



# ----------------------------
# Tenant Request Admin
# ----------------------------
@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
    list_display = ('tenant_name', 'desired_domain', 'is_approved', 'requested_on')
    list_filter = ('status',)
    actions = ['approve_selected_tenants']
    print("🔍 TenantRequestAdmin loaded successfully")

    @admin.action(description='Approve selected tenants')
    def approve_selected_tenants(self, request, queryset):
        try:
            print("🚀 ACTION EXECUTED >>>", queryset)
            connection.set_autocommit(True)
    
            with schema_context('public'):
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
                        email=tenant_request.email,
                        company=tenant_request.company,
                        address=tenant_request.address,
                        logo=tenant_request.logo
                    )
                    tenant.save()  # just saves metadata first
    
                    print(f"⚙️ Creating schema manually for: {schema_name}")
                    tenant.create_schema(check_if_exists=True)  # ✅ force schema creation
    
                    Domain.objects.create(
                        domain=f"{tenant_request.desired_domain}.localhost",
                        tenant=tenant,
                        is_primary=True
                    )
    
                    print(f"✅ Tenant {schema_name} schema created successfully.")
    
            connection.set_autocommit(False)
            self.message_user(request, "✅ Tenants approved and schemas created successfully.")
        except Exception as e:
            import traceback
            traceback.print_exc()
            self.message_user(request, f"❌ Error approving tenants: {e}", level='error')


# ----------------------------
# Other Admin Registrations
# ----------------------------

@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'storage_limit_mb', 'status')
    list_filter = ('status',)
    search_fields = ('name',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('client', 'subject', 'category', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('category', 'priority', 'status')
    search_fields = ('client__tenant_name', 'subject', 'assigned_to')


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('client', 'amount', 'method', 'payment_plan', 'status', 'transaction_id', 'created_at')
    list_filter = ('method', 'payment_plan', 'status')
    search_fields = ('client__tenant_name', 'transaction_id')


@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('client', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'plan', 'auto_renew')
    search_fields = ('client__tenant_name', 'plan__name')
    ordering = ['-end_date']  # reflect latest subscription first


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number', 'client', 'subscription', 'payment', 'invoice_type', 'created_at')
    list_filter = ('invoice_type',)
    search_fields = ('invoice_number', 'client__tenant_name')


@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ('client', 'payment', 'refund_type', 'refund_policy', 'status', 'refund_amount', 'requested_at')
    list_filter = ('status', 'refund_type', 'refund_policy')
    search_fields = ('client__tenant_name', 'payment__transaction_id')
