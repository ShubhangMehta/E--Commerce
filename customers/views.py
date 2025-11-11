from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Plan, Subscription, Invoice, Payment, Refund
from django.utils import timezone
import json


def home(request):
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'billing/home.html', {'plans': plans})


def plans(request):
    plans = Plan.objects.filter(is_active=True)
    return render(request, 'billing/plans.html', {'plans': plans})

def billing_cycle(request):
    subscriptions = Subscription.objects.filter(tenant__user=request.user)
    invoices = Invoice.objects.filter(subscription__in=subscriptions)
    return render(request, 'billing/billing_cycle.html', {
        'subscriptions': subscriptions,
        'invoices': invoices
    })

@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(Plan, id=plan_id, is_active=True)
    if request.method == 'POST':
        # Process payment and create subscription
        subscription = Subscription.objects.create(
            tenant=request.user.tenant,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=30),
            next_due_date=timezone.now() + timezone.timedelta(days=30)
        )
        
        # Create invoice
        invoice = Invoice.objects.create(
            subscription=subscription,
            amount=plan.price,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        return redirect('payment_success', invoice_id=invoice.id)
    
    return render(request, 'billing/checkout.html', {'plan': plan})

@login_required
def payment_success(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    return render(request, 'billing/payment_success.html', {'invoice': invoice})

@login_required
def subscription(request):
    subscriptions = Subscription.objects.filter(tenant__user=request.user)
    return render(request, 'billing/subscription.html', {'subscriptions': subscriptions})

@login_required
def renew_subscription(request, subscription_id):
    subscription = get_object_or_404(Subscription, id=subscription_id, tenant__user=request.user)
    
    if request.method == 'POST':
        # Process renewal payment
        invoice = Invoice.objects.create(
            subscription=subscription,
            amount=subscription.plan.price,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )
        
        return redirect('payment_success', invoice_id=invoice.id)
    
    return render(request, 'billing/renew.html', {'subscription': subscription})

def update_plan(request, subscription_id):
    if request.method == 'POST':
        data = json.loads(request.body)
        subscription = get_object_or_404(Subscription, id=subscription_id)
        new_plan = get_object_or_404(Plan, id=data['plan_id'])
        
        subscription.plan = new_plan
        subscription.save()
        
        return JsonResponse({'success': True, 'message': 'Plan updated successfully'})

def mark_invoice_paid(request, invoice_id):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, id=invoice_id)
        invoice.status = 'paid'
        invoice.paid_date = timezone.now()
        invoice.save()
        
        return JsonResponse({'success': True, 'message': 'Invoice marked as paid'})
        
