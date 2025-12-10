from django.contrib import admin
from django.db import connection
from django.utils import timezone
from django_tenants.utils import schema_context
from .models import (
    SubscriptionPlan,
    ClientRefundRequest,
    Client,
    Domain,
    TenantRequest,

    # Razorpay related models
    RzpPlan,
    RzpSubscription,
    RzpInvoice,
    RzpPayment,
    RzpWebhookEvent,
    RzpRefund,
)


# -----------------------------
# Subscription Plan Admin
# -----------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "duration_days", "status"]
    list_filter = ["status"]
    search_fields = ["name", "description"]


# -----------------------------
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
    list_display = ("razorpay_payment_id", "subscription", "amount_in_paise", "captured")


@admin.register(RzpWebhookEvent)
class RzpWebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "signature_ok", "received_at")


@admin.register(RzpRefund)
class RzpRefundAdmin(admin.ModelAdmin):
    list_display = ("payment", "razorpay_refund_id", "status", "created_at")
