from django.contrib import admin, messages
from unfold.admin import ModelAdmin   # ✓ Unfold Admin
from django.db import connection
from django_tenants.utils import schema_context
from django.db import transaction
from .models import (
    Client, Domain, TenantRequest, SubscriptionPlan,
    Ticket, ClientSubscription, Invoice,
    RzpPayment, RzpWebhookEvent, RzpRefund, PlanPricing, RazorpayOrderMap
)
from django.utils import timezone
from datetime import timedelta
from core_app.emails.utils import send_html_email
from customers.services.provisioning import provision_tenant_from_request


# ----------------------------
# Client Admin
# ----------------------------
@admin.register(Client)
class ClientAdmin(ModelAdmin):
    list_display = (
        'tenant_name',
        'status',
        'theme',
        'current_plan',
        'subscription_start',
        'subscription_end',
        'catalog_template',
        
    )

    readonly_fields = (
        'created_on',
        'status',
        'current_plan',
        'subscription_start',
        'subscription_end',
        'used_trial',
        'storage_used_mb',
        'product_count',
        'order_count',
        'visitor_count_7d',
        'visitor_count_30d',
        'active_users',
        'last_login',
    )

    list_filter = ('desired_domain','theme', 'catalog_template')
    search_fields = ('tenant_name', 'schema_name')
    ordering = ('-clientsubscription__start_date',)



# ----------------------------
# Domain Admin
# ----------------------------
@admin.register(Domain)
class DomainAdmin(ModelAdmin):
    list_display = ('domain', 'tenant_owner_name', 'tenant_name_display', 'is_primary', 'tenant_status_display')
    list_filter = ('is_primary',)
    search_fields = ('desired_domain', 'tenant__tenant_name')

    def tenant_owner_name(self, obj):
        return obj.tenant.owner_name
    tenant_owner_name.short_description = 'Owner Name'

    def tenant_name_display(self, obj):
        return obj.tenant.tenant_name
    tenant_name_display.short_description = 'Tenant Name'
    
    def tenant_status_display(self, obj):
        return obj.tenant.status
    tenant_status_display.short_description = 'Status'



# ----------------------------
# Tenant Request Admin
# ----------------------------
@admin.register(TenantRequest)
class TenantRequestAdmin(ModelAdmin):
    list_display = ('tenant_name', 'desired_domain', 'owner_name', 'requested_on')
    list_filter = ('status',)
    actions = ['provision_tenant']

    @admin.action(description="Provision tenant ")
    def provision_tenant(modeladmin, request, queryset):
        success = 0
        failed = 0

        for tr in queryset:
            if tr.status == "approved":
                modeladmin.message_user(
                    request,
                    f"{tr.desired_domain} already provisioned",
                    level=messages.WARNING
                )
                continue

            try:
                with transaction.atomic():
                    tenant, domain, subscription = provision_tenant_from_request(
                        tenant_request=tr,
                        plan=tr.plan,
                        pricing=tr.pricing,
                    )

                    tr.status = "approved"
                    tr.save(update_fields=["status"])

                    success += 1

            except Exception as e:
                failed += 1
                modeladmin.message_user(
                    request,
                    f"Failed to provision {tr.desired_domain}: {e}",
                    level=messages.ERROR
                )

        modeladmin.message_user(
            request,
            f"Provisioning complete. Success: {success}, Failed: {failed}",
            level=messages.INFO
        )


    # @admin.action(description='Provision Tenant')
    # def provision_tenant(self, request, queryset):
    #     try:
    #         connection.set_autocommit(True)

    #         with schema_context('public'):
    #             for tr in queryset.filter(is_approved=False):
    #                 schema_name = tr.tenant_name.lower().replace(" ", "_")
    #                 pricing = tr.pricing
                        
    #                 # Mark approved ONLY if valid
    #                 tr.is_approved = True
    #                 tr.status = "Approved"
    #                 tr.save()

    #                 # Create Tenant
    #                 tenant = Client.objects.create(
    #                     schema_name=schema_name,
    #                     tenant_name=tr.tenant_name,
    #                     server_name="VPS-001",
    #                     desired_domain=tr.desired_domain,
    #                     email=tr.email,
    #                     company=tr.company,
    #                     address=tr.address,
    #                     logo=tr.logo,
    #                     theme=tr.theme
    #                 )
                    
    #                 tenant.create_schema(check_if_exists=True)

    #                 # Create Domain
    #                 Domain.objects.create(
    #                     domain=f"{tr.desired_domain}.localhost",
    #                     tenant=tenant,
    #                     is_primary=True
    #                 )

    #                 # Subscription
    #                 start_date = timezone.now()
    #                 end_date = start_date + timedelta(days=pricing.duration_days)
                    
    #                 plan=pricing.plan
    #                 ClientSubscription.objects.create(
    #                     client=tenant,
    #                     plan=plan,
    #                     pricing=pricing,
    #                     #payment=payment,
    #                     start_date=start_date,
    #                     end_date=end_date,
    #                     status = 'Active'
    #                     #auto_renew=not pricing.is_trial
    #                 )
                
    #                 print(f"✅ Subscription created for tenant: {tenant.tenant_name}")
    #                 if tr.email:
    #                     send_html_email(
    #                         subject="Your Tenant has been successfully created",
    #                         to_email=tr.email,
    #                         template_name="emails/tenant_created.html",
    #                         context={
    #                             "owner_name": tr.tenant_name,
    #                             "tenant_name": tr.tenant_name,
    #                             "company": tr.company,
    #                             "email": tr.email,
    #                             "address": tr.address,
    #                             #"created_on": tenant_created_on,
    #                             "domain": tr.desired_domain,
    #                         }
    #                     )
    #                     print(f"email sent to {tr.email}")   
    #                 else:
    #                         print(f"⚠️ No email provided for tenant request ID {tr.id}, skipping email notification.")
    #                         continue
                    
    #         connection.set_autocommit(False)
    #         self.message_user(request, "🎉 Tenants approved and all resources created successfully.")

    #     except Exception as e:
    #         import traceback
    #         traceback.print_exc()
    #         self.message_user(request, f"❌ Error approving tenants: {e}", level='error')


# ----------------------------
# Other Admin Registrations
# ----------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(ModelAdmin):
    list_display = ('name', 'storage_limit_mb', 'status')
    list_filter = ('status',)   #Dont delete comma , it becomes a string
    search_fields = ('name',)   #Dont delete comma , it becomes a string


@admin.register(Ticket)
class TicketAdmin(ModelAdmin):
    list_display = ('client', 'subject', 'category', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter = ('category', 'priority', 'status')
    search_fields = ('client__tenant_name', 'subject', 'assigned_to')


@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(ModelAdmin):
    list_display = ('client', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'plan', 'auto_renew')
    search_fields = ('client__tenant_name', 'plan__name')
    ordering = ['-end_date']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('invoice_number',
                    'tenant_request', 
                    'status', 
                    'amount', 
                    'razorpay_order_id',
                    'created_at'
                    )
    list_filter = ('status',)
    search_fields = ('invoice_number', 'razorpay_order_id', 'tenant_request__desired_domain')

    def has_add_permission(self, request):
        return False
    


@admin.register(PlanPricing)
class PlanPricingAdmin(ModelAdmin):
    list_display = ('plan', 'billing_cycle', 'price', 'duration_days')
    list_filter = ('plan', 'billing_cycle')
    search_fields = ('plan__name',)
    ordering = ('plan', 'billing_cycle')

# -----------------------------
# Razorpay Related Admin Models
# -----------------------------

@admin.register(RzpPayment)
class RzpPaymentAdmin(admin.ModelAdmin):
    list_display = (
        "razorpay_payment_id",
        "invoice",
        "status",
        "event",
        "captured",
        "created_at",
    )

    list_filter = ("status", "captured", "event")
    search_fields = ("razorpay_payment_id", "razorpay_order_id")
    readonly_fields = ("created_at",)

    def has_add_permission(self, request):
        return False


@admin.register(RzpWebhookEvent)
class RzpWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "created_at")
    readonly_fields = ("event", "payload", "created_at")
    ordering = ("-created_at",)
    
    def has_add_permission(self, request):
        return False


@admin.register(RzpRefund)
class RzpRefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "razorpay_refund_id", "status", "created_at")

@admin.register(RazorpayOrderMap)
class RazorpayOrderMapAdmin(admin.ModelAdmin):
    list_display = ("local_order_id", "razorpay_order_id", "tenant")
    search_fields = ("local_order_id", "razorpay_order_id", "tenant__tenant_name")
