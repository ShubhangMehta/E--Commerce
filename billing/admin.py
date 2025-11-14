from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, WebhookEvent

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ("name", "interval", "amount_in_paise", "razorpay_plan_id")

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("tenant_name", "desired_domain", "email", "plan", "status",
                    "current_period_start", "current_period_end", "razorpay_subscription_id")

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("number", "subscription", "amount_in_paise", "status", "issued_at", "paid_at")

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("razorpay_payment_id", "subscription", "amount_in_paise", "captured", "created_at")

@admin.register(WebhookEvent)
class WebhookEventAdmin(admin.ModelAdmin):
    list_display = ("event", "signature_ok", "received_at")
