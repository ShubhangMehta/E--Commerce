from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from django.db import connection
from django_tenants.utils import schema_context
from .models import (
    Client, Domain, TenantRequest, SubscriptionPlan,
    Ticket, ClientSubscription, Payment, Invoice, RefundRequest,
    RzpPayment, RzpWebhookEvent, RzpRefund
)
from django.utils import timezone
from core_app.emails.utils import send_html_email


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
    )



# ----------------------------
# Tenant Request Admin
# ----------------------------
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
                for tr in queryset.filter(is_approved=False):
                    schema_name = tr.tenant_name.lower().replace(" ", "_")

                    # 1️⃣ Mark request approved
                    tr.is_approved = True
                    tr.status = "Approved"
                    tr.save()

                    # 2️⃣ Create Tenant
                    tenant = Client.objects.create(
                        schema_name=schema_name,
                        tenant_name=tr.tenant_name,
                        server_name="VPS-001",
                        desired_domain=tr.desired_domain,
                        email=tr.email,
                        company=tr.company,
                        address=tr.address,
                        logo=tr.logo
                    )


                    print(f"⚙️ Creating schema manually for: {schema_name}")
                    tenant.create_schema(check_if_exists=True)

                    # 3️⃣ Create Domain
                    domain = Domain.objects.create(
                        domain=f"{tr.desired_domain}.localhost",
                        tenant=tenant,
                        is_primary=True
                    )

                    # 4️⃣ Create Payment
                    amount = tr.plan.price
                    payment = Payment.objects.create(
                        client=tenant,
                        amount=amount,
                        method=tr.payment_mode,
                        payment_plan=tr.payment_plan,
                        transaction_id=f"TXN-{tenant.id}-{timezone.now().timestamp()}",
                        status='paid'
                    )

                    # 5️⃣ Create Subscription
                    subscription = ClientSubscription.objects.create(
                        client=tenant,
                        plan=tr.plan,
                        payment=payment,
                        auto_renew=True
                    )

                    print(f"✅ Subscription created for tenant: {tenant.tenant_name}")
                    
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
                    if not tr.email:
                            print(f"⚠️ No email provided for tenant request ID {tr.id}, skipping email notification.")
                            continue
                       
                    print(f"email sent to {tr.email}")

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
