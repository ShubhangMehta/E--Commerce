from django.contrib import admin
from .models import (
    Customer,
    SubscriptionPlan,
    UserSubscription,
    Payment,
    Invoice,
    RefundRequest,
    Client,
    Domain
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
# Payment Admin
# -----------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["user", "amount", "method", "payment_plan", "transaction_id", "status", "created_at"]
    search_fields = ["user__username", "transaction_id"]
    list_filter = ["method", "payment_plan", "status"]
    readonly_fields = ["created_at"]


# -----------------------------
# Invoice Admin
# -----------------------------
@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ["invoice_number", "user", "subscription", "payment", "invoice_type", "created_at"]
    search_fields = ["invoice_number", "user__username"]
    list_filter = ["invoice_type"]
    readonly_fields = ["created_at"]


# -----------------------------
# Refund Request Admin
# -----------------------------
@admin.register(RefundRequest)
class RefundRequestAdmin(admin.ModelAdmin):
    list_display = ["user", "payment", "refund_type", "refund_policy", "status", "requested_at", "is_refunded"]
    search_fields = ["user__username", "reason"]
    list_filter = ["refund_type", "refund_policy", "status", "is_refunded"]


# -----------------------------
# Tenant & Domain Admin (django-tenants)
# -----------------------------
@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ["tenant_name", "server_name", "desired_domain", "paid_until", "on_trial", "created_on"]


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ["domain", "tenant", "is_primary"]
