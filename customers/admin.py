from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Client, Domain, TenantRequest
from datetime import date
from django.db import connection, transaction
from django_tenants.utils import schema_context
from core_app.emails.utils import send_html_email


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant_name_display', 'is_primary', 'tenant_status_display')
    list_filter = ('is_primary', 'tenant__status') 
    search_fields = ('desired_domain', 'tenant__tenant_name', 'tenant__schema_name')

    def tenant_name_display(self, obj):
        return obj.tenant.tenant_name
    tenant_name_display.short_description = 'Tenant Name'
    
    def tenant_status_display(self, obj):
        return obj.tenant.status
    tenant_status_display.short_description = 'Status'
    
@admin.register(Client)
class ClientAdmin(TenantAdminMixin, admin.ModelAdmin):
    # --- A. List Display (The Tenant Overview Dashboard) ---
    list_display = (
        'tenant_name', 
        'schema_name', 
        'status',          # Active/Suspended
        'plan_type',       
        'subscription_end',
        'display_payment_due', # Custom indicator for next due date
        'display_usage_summary', # Custom method for key metrics
        'created_on',
    )
    
    # --- B. Filters, Search, and Sorting ---
    list_filter = ('status', 'plan_type')
    search_fields = ('tenant_name', 'schema_name')
    # Sort by creation date by default
    ordering = ('-created_on',)
    
    # --- C. Field Organization (For the Detail/Edit Page) ---
    # Organize fields into collapsible sections for clarity
    fieldsets = (
        ('🏢 Core Tenant Information', {
            'fields': (('tenant_name', 'schema_name'), 'server_name', 'desired_domain', 'status'),
        }),
        ('💳 Subscription & Billing', {
            'fields': (('plan_type', 'subscription_end'), 'last_payment_date', 'next_due_date', 'total_orders_value'),
        }),
        ('📊 Usage & Performance Metrics', {
            'fields': (('storage_used_mb', 'product_count', 'order_count'), ('visitor_count_7d', 'visitor_count_30d', 'active_users', 'last_login')),
            'classes': ('collapse',), # Make this section collapsible
        }),
        ('💰 Payment Processing', {
            'fields': (('payment_mode', 'payment_status')),
            'classes': ('collapse',),
        }),
    )
    
    # --- D. Admin Actions (Tenant Management Workflow) ---
    actions = ['suspend_tenants', 'activate_tenants']

    # Custom action to suspend a tenant
    def suspend_tenants(self, request, queryset):
        updated = queryset.update(status='Suspended')
        self.message_user(request, f"{updated} tenant(s) successfully suspended and access disabled.")
    suspend_tenants.short_description = "Suspend selected tenants"

    # Custom action to activate a tenant
    def activate_tenants(self, request, queryset):
        updated = queryset.update(status='Active')
        self.message_user(request, f"{updated} tenant(s) successfully activated.")
    activate_tenants.short_description = "Activate selected tenants"

    # --- E. Custom Display Methods for the List View ---
    
    def display_usage_summary(self, obj):
        """Displays key metrics in a compact format."""
        # Use HTML formatting to make the data stand out in the list view
        return (
            f"**P**: {obj.product_count} | "
            f"**O**: {obj.order_count} | "
            f"**St**: {round(obj.storage_used_mb, 1)}MB"
        )
    display_usage_summary.short_description = 'Usage (P|O|Storage)'
    
    def display_payment_due(self, obj):
        """Highlights the next due date."""
        if obj.next_due_date:
            return f"Due: {obj.next_due_date}"
        return "N/A"
    display_payment_due.short_description = 'Next Due'
    
    # --- F. Read-Only Fields ---
    # These fields should only be managed by the system, not manually edited by the Super Admin
    readonly_fields = (
        'created_on', 'subscription_start', 'storage_used_mb', 
        'product_count', 'order_count', 'visitor_count_7d', 
        'visitor_count_30d', 'active_users', 'last_login', 
        'total_orders_value', 'last_payment_date'
    )

@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
    list_display = ('tenant_name', 'desired_domain', 'is_approved', 'requested_on')
    list_filter = ('status',)
    actions = ['approve_selected_tenants']
    #print("🔍 TenantRequestAdmin loaded successfully")

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
                        plan_type=tenant_request.plan_type,
                        payment_mode=tenant_request.payment_mode,
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
                    
                    send_html_email(
                        subject="Your Tenant has been successfully created",
                        to_email=tenant_request.email,
                        template_name="emails/tenant_created.html",
                        context={
                            "owner_name": tenant_request.tenant_name,
                            "tenant_name": tenant_request.tenant_name,
                            "company": tenant_request.company,
                            "email": tenant_request.email,
                            "address": tenant_request.address,
                            #"created_on": tenant_created_on,
                            "domain": tenant_request.desired_domain
                        }
                    )       
                    print(f" email sent to {tenant_request.email}")
    
            connection.set_autocommit(False)
            self.message_user(request, "✅ Tenants approved and schemas created successfully.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.message_user(request, f"❌ Error approving tenants: {e}", level='error')