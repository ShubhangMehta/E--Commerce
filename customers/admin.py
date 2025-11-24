from django.contrib import admin
from .models import (
    Customer,
    SubscriptionPlan,
    UserSubscription,
    UserPayment,
    UserInvoice,
    UserRefundRequest,
    Client,
    Domain,

    # Razorpay related models
    RzpPlan,
    RzpSubscription,
    RzpInvoice,
    RzpPayment,
    RzpWebhookEvent,
    RzpRefund,
)

# -----------------------------
# Customer Admin
# -----------------------------
@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "phone", "joined_date"]
    search_fields = ["name", "email", "phone"]
    list_filter = ["joined_date"]


# -----------------------------
# Subscription Plan Admin
# -----------------------------
@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ["name", "price", "duration_days", "status"]
    list_filter = ["status"]
    search_fields = ["name", "description"]


# -----------------------------
# User Subscription Admin
# -----------------------------
@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    list_display = ["user", "plan", "start_date", "end_date", "status", "is_active", "auto_renew"]
    list_filter = ["status", "is_active", "auto_renew"]
    search_fields = ["user__username", "plan__name"]


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


# -----------------------------
# User Refund Request Admin
# -----------------------------
@admin.register(UserRefundRequest)
class UserRefundRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "payment", "refund_type", "refund_policy", "status", "requested_at", "is_refunded"]
    search_fields = ["user__username", "reason"]
    list_filter = ["refund_type", "refund_policy", "status", "is_refunded"]


# -----------------------------
# Tenant & Domain Admin
# -----------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["tenant_name", "server_name", "desired_domain", "paid_until", "on_trial", "created_on"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]


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
