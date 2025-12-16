from django.contrib import admin
<<<<<<< HEAD
<<<<<<< HEAD
=======
=======
from django.db import connection
from django.utils import timezone
from django_tenants.utils import schema_context
>>>>>>> 304533d (cleaned the unwanted files and folders)
from .models import (
    SubscriptionPlan,
    ClientRefundRequest,
    Client,
    Domain,
<<<<<<< HEAD
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
=======
    TenantRequest,
>>>>>>> 304533d (cleaned the unwanted files and folders)

# Register your models here.
from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, Refund

<<<<<<< HEAD
<<<<<<< HEAD
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'plan_type', 'price', 'billing_cycle', 'is_active']
    list_filter = ['plan_type', 'billing_cycle', 'is_active']
    search_fields = ['name', 'description']
    list_editable = ['is_active']

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'plan', 'status', 'start_date', 'end_date', 'next_due_date']
    list_filter = ['status', 'plan', 'auto_renew']
    search_fields = ['tenant__name', 'plan__name']
    readonly_fields = ['created_at']
=======
# -----------------------------
# Customer Admin
# -----------------------------
'''
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "joined_date"]
    search_fields = ["name", "email", "phone"]
    list_filter = ["joined_date"]

'''
>>>>>>> 69fec36 (Razorpay Integration)
=======
>>>>>>> 304533d (cleaned the unwanted files and folders)

<<<<<<< HEAD
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status', 'due_date']
    search_fields = ['invoice_number', 'subscription__tenant__name']
    readonly_fields = ['created_at']
    actions = ['mark_as_paid', 'generate_pdf_invoices']
=======
# -----------------------------
# Subscription Plan Admin
# -----------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "duration_days", "status"]
    list_filter = ["status"]
    search_fields = ["name", "description"]


# -----------------------------
<<<<<<< HEAD
# User Subscription Admin
# -----------------------------
'''
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "start_date", "end_date", "status", "is_active", "auto_renew"]
    list_filter = ["status", "is_active", "auto_renew"]
    search_fields = ["user__username", "plan__name"]
'''


'''
# -----------------------------
# User Payment Admin
# -----------------------------
@admin.register(UserPayment)
class UserPaymentAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "method", "payment_plan", "transaction_id", "status", "created_at"]
    search_fields = ["user__username", "transaction_id"]
    list_filter = ["method", "payment_plan", "status"]
    readonly_fields = ["created_at"]


# -----------------------------
# User Invoice Admin
# -----------------------------
@admin.register(UserInvoice)
class UserInvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "user", "subscription", "payment", "invoice_type", "created_at"]
    search_fields = ["invoice_number", "user__username"]
    list_filter = ["invoice_type"]
    readonly_fields = ["created_at"]
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', paid_date=timezone.now())
        self.message_user(request, f'{updated} invoices marked as paid.')
    mark_as_paid.short_description = "Mark selected invoices as paid"

<<<<<<< HEAD
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'invoice', 'payment_method', 'amount', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['transaction_id', 'invoice__invoice_number']
    readonly_fields = ['payment_date']
=======
# -----------------------------
# User Refund Request Admin
# -----------------------------
@admin.register(UserRefundRequest)
class UserRefundRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "payment", "refund_type", "refund_policy", "status", "requested_at", "is_refunded"]
    search_fields = ["user__username", "reason"]
    list_filter = ["refund_type", "refund_policy", "status", "is_refunded"]
<<<<<<< HEAD
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
=======
    
'''
>>>>>>> 69fec36 (Razorpay Integration)

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'status', 'created_at', 'approved_by']
    list_filter = ['status', 'created_at']
    search_fields = ['subscription__tenant__name', 'reason']
    readonly_fields = ['created_at']
    actions = ['approve_refunds', 'reject_refunds']

<<<<<<< HEAD
    def approve_refunds(self, request, queryset):
        updated = queryset.update(status='approved', approved_by=request.user, approved_date=timezone.now())
        self.message_user(request, f'{updated} refunds approved.')
    approve_refunds.short_description = "Approve selected refunds"
=======
# -----------------------------
=======
>>>>>>> 304533d (cleaned the unwanted files and folders)
# Tenant & Domain Admin
# -----------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["tenant_name", "server_name", "desired_domain", "status", "current_plan", "created_on"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]


@admin.register(TenantRequest)
class TenantRequestAdmin(admin.ModelAdmin):
    list_display = ('tenant_name', 'desired_domain', 'is_approved', 'requested_on')
    list_filter = ('status',)
    actions = ['approve_selected_tenants']

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

                    # 2️⃣ Create Tenant (Client)
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
                    Domain.objects.create(
                        domain=f"{tr.desired_domain}.localhost",
                        tenant=tenant,
                        is_primary=True
                    )

                    # 4️⃣ Create Razorpay Subscription
                    rzp_subscription = RzpSubscription.objects.create(
                        client=tenant,
                        tenant_name=tenant.tenant_name,
                        desired_domain=tenant.desired_domain,
                        email=tenant.email,
                        plan=tr.plan,  
                        interval="monthly",  # you can use tr.payment_plan instead
                        status="created"
                    )

                    # 5️⃣ Create Razorpay Payment (mock successful payment)
                    rzp_payment = RzpPayment.objects.create(
                        subscription=rzp_subscription,
                        amount_in_paise=int(tr.plan.price * 100),  # INR → paise
                        razorpay_payment_id=f"pay_{tenant.id}_{int(timezone.now().timestamp())}",
                        currency="INR",
                        captured=True
                    )

                    print(f"💰 Payment & Subscription created for tenant: {tenant.tenant_name}")

            connection.set_autocommit(False)
            self.message_user(request, "🎉 Tenants approved and Razorpay subscription created successfully!")

        except Exception as e:
            import traceback
            traceback.print_exc()
            self.message_user(request, f"❌ Error approving tenants: {e}", level='error')


@admin.register(ClientRefundRequest)
class ClientRefundRequestAdmin(admin.ModelAdmin):
    list_display = (
        "client",
        "payment",
        "refund_amount",
        "refund_type",
        "refund_policy",
        "status",
        "requested_at",
        "processed_at",
    )
    list_filter = ("status", "refund_type", "refund_policy")
    search_fields = ("client__tenant_name", "reason", "payment__transaction_id")

# -----------------------------
# Razorpay Related Admin Models
# -----------------------------

@admin.register(RzpPlan)
class RzpPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "interval", "amount_in_paise")


@admin.register(RzpSubscription)
class RzpSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("email", "plan", "status", "current_period_start", "current_period_end")


@admin.register(RzpInvoice)
class RzpInvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "subscription", "amount_in_paise", "status")


@admin.register(RzpPayment)
class RzpPaymentAdmin(admin.ModelAdmin):
    list_display = ("razorpay_payment_id", "subscription", "amount", "captured")


@admin.register(RzpWebhookEvent)
class RzpWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "signature_ok", "received_at")


@admin.register(RzpRefund)
class RzpRefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "razorpay_refund_id", "status", "created_at")
>>>>>>> defaf09 (subscription and billing integration(razorpay) changed from billing app to customers app)
