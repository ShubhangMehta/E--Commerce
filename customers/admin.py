from django.contrib import admin
from unfold.admin import ModelAdmin   # ✓ Unfold Admin
from django.db import connection
from django.contrib import messages
from django_tenants.utils import schema_context
from .models import (
    Client, Domain, TenantRequest, SubscriptionPlan,
    Ticket, ClientSubscription, Invoice,
    RzpPayment, RzpWebhookEvent, RzpRefund, PlanPricing
)
from django.utils import timezone
from datetime import timedelta
from core_app.emails.utils import send_html_email

# ----------------------------
# Domain Admin
# ----------------------------
@admin.register(Domain)
class DomainAdmin(ModelAdmin):
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
class ClientAdmin(ModelAdmin):
    list_display = (
        'tenant_name',
        'schema_name',
        'status',
        'theme',
        'current_plan',
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

    list_filter = ('desired_domain','theme')
    search_fields = ('tenant_name', 'schema_name')
    ordering = ('-clientsubscription__start_date',)

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
        ('🎨 Branding & Theme', {
            'fields': ('theme',),
            }),
    )


# ----------------------------
# Tenant Request Admin
# ----------------------------
@admin.register(TenantRequest)
class TenantRequestAdmin(ModelAdmin):
    list_display = ('tenant_name', 'desired_domain', 'is_approved', 'requested_on')
    list_filter = ('status',)
    actions = ['approve_selected_tenants']

    @admin.action(description='Approve selected tenants')
    def approve_selected_tenants(self, request, queryset):
        try:
            connection.set_autocommit(True)

            with schema_context('public'):
                for tr in queryset.filter(is_approved=False):
                    schema_name = tr.tenant_name.lower().replace(" ", "_")
                    pricing = tr.pricing
                        
                    # Mark approved ONLY if valid
                    tr.is_approved = True
                    tr.status = "Approved"
                    tr.save()

                    # Create Tenant
                    tenant = Client.objects.create(
                        schema_name=schema_name,
                        tenant_name=tr.tenant_name,
                        server_name="VPS-001",
                        desired_domain=tr.desired_domain,
                        email=tr.email,
                        company=tr.company,
                        address=tr.address,
                        logo=tr.logo,
                        theme=tr.theme
                    )
                    
                    tenant.create_schema(check_if_exists=True)

                    # Create Domain
                    Domain.objects.create(
                        domain=f"{tr.desired_domain}.localhost",
                        tenant=tenant,
                        is_primary=True
                    )

                    # # Payment
                    # if pricing.is_trial:
                    #     amount = 0
                    #     payment_status = 'trial'
                    # else:
                    #     amount = pricing.price
                    #     payment_status = 'paid'
                    
                    # payment = Payment.objects.create(
                    #     client=tenant,
                    #     amount=amount,
                    #     payment_plan=pricing.billing_cycle,
                    #     transaction_id=f"TXN-{tenant.id}-{timezone.now().timestamp()}",
                    #     status=payment_status
                    # )
                    # Subscription
                    start_date = timezone.now()
                    end_date = start_date + timedelta(days=pricing.duration_days)
                    
                    plan=pricing.plan
                    ClientSubscription.objects.create(
                        client=tenant,
                        plan=plan,
                        pricing=pricing,
                        #payment=payment,
                        start_date=start_date,
                        end_date=end_date,
                        status = 'Active'
                        #auto_renew=not pricing.is_trial
                    )
                    # if pricing.is_trial:
                    #     tenant.has_used_trial = True
                    #     tenant.save()
                   

                    print(f"✅ Subscription created for tenant: {tenant.tenant_name}")
                    if tr.email:
                        send_html_email(
                            subject="Your Tenant has been successfully created",
                            to_email=tr.email,
                            template_name="emails/tenant_created.html",
                            context={
                                "owner_name": tr.tenant_name,
                                "tenant_name": tr.tenant_name,
                                "company": tr.company,
                                "email": tr.email,
                                "address": tr.address,
                                #"created_on": tenant_created_on,
                                "domain": tr.desired_domain,
                            }
                        )
                        print(f"email sent to {tr.email}")   
                    else:
                            print(f"⚠️ No email provided for tenant request ID {tr.id}, skipping email notification.")
                            continue
            connection.set_autocommit(False)
            self.message_user(request, "🎉 Tenants approved and all resources created successfully.")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.message_user(request, f"❌ Error approving tenants: {e}", level='error')


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


# @admin.register(Payment)
# class PaymentAdmin(ModelAdmin):
#     list_display = ('client', 'amount', 'payment_plan', 'status', 'transaction_id', 'created_at')
#     list_filter = ('payment_plan', 'status')
#     search_fields = ('client__tenant_name', 'transaction_id')


@admin.register(ClientSubscription)
class ClientSubscriptionAdmin(ModelAdmin):
    list_display = ('client', 'plan', 'status', 'start_date', 'end_date', 'auto_renew')
    list_filter = ('status', 'plan', 'auto_renew')
    search_fields = ('client__tenant_name', 'plan__name')
    ordering = ['-end_date']


@admin.register(Invoice)
class InvoiceAdmin(ModelAdmin):
    list_display = ('invoice_number', 'client', 'subscription', 'payment', 'invoice_type', 'created_at')
    list_filter = ('invoice_type',)
    search_fields = ('invoice_number', 'client__tenant_name')


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
    list_display = ("razorpay_payment_id", "subscription", "amount", "captured")


@admin.register(RzpWebhookEvent)
class RzpWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "signature_ok", "received_at")


@admin.register(RzpRefund)
class RzpRefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "razorpay_refund_id", "status", "created_at")
