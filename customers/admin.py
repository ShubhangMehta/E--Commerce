from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Plan, Subscription, Invoice, Payment, Refund

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

@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'subscription', 'amount', 'status', 'due_date', 'paid_date']
    list_filter = ['status', 'due_date']
    search_fields = ['invoice_number', 'subscription__tenant__name']
    readonly_fields = ['created_at']
    actions = ['mark_as_paid', 'generate_pdf_invoices']

    def mark_as_paid(self, request, queryset):
        updated = queryset.update(status='paid', paid_date=timezone.now())
        self.message_user(request, f'{updated} invoices marked as paid.')
    mark_as_paid.short_description = "Mark selected invoices as paid"

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['transaction_id', 'invoice', 'payment_method', 'amount', 'payment_date']
    list_filter = ['payment_method', 'payment_date']
    search_fields = ['transaction_id', 'invoice__invoice_number']
    readonly_fields = ['payment_date']

@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin):
    list_display = ['subscription', 'amount', 'status', 'created_at', 'approved_by']
    list_filter = ['status', 'created_at']
    search_fields = ['subscription__tenant__name', 'reason']
    readonly_fields = ['created_at']
    actions = ['approve_refunds', 'reject_refunds']

    def approve_refunds(self, request, queryset):
        updated = queryset.update(status='approved', approved_by=request.user, approved_date=timezone.now())
        self.message_user(request, f'{updated} refunds approved.')
    approve_refunds.short_description = "Approve selected refunds"