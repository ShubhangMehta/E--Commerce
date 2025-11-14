from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json

from .models import SubscriptionPlan, UserSubscription, Invoice, Payment


def home(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'billing/home.html', {'plans': plans})


def plans(request):
    plans = SubscriptionPlan.objects.filter(is_active=True)
    return render(request, 'billing/plans.html', {'plans': plans})


@login_required
def billing_cycle(request):
    subscriptions = UserSubscription.objects.filter(user=request.user)
    invoices = Invoice.objects.filter(subscription__in=subscriptions)
    return render(request, 'billing/billing_cycle.html', {
        'subscriptions': subscriptions,
        'invoices': invoices
    })


@login_required
def checkout(request, plan_id):
    plan = get_object_or_404(SubscriptionPlan, id=plan_id)

    if request.method == 'POST':
        # Create subscription
        subscription = UserSubscription.objects.create(
            user=request.user,
            plan=plan,
            status='active',
            start_date=timezone.now(),
            end_date=timezone.now() + timezone.timedelta(days=plan.duration_days),
            next_due_date=timezone.now() + timezone.timedelta(days=plan.duration_days)
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
    subscriptions = UserSubscription.objects.filter(user=request.user)
    return render(request, 'billing/subscription.html', {'subscriptions': subscriptions})


@login_required
def renew_subscription(request, subscription_id):
    subscription = get_object_or_404(UserSubscription, id=subscription_id, user=request.user)

    if request.method == 'POST':
        invoice = Invoice.objects.create(
            subscription=subscription,
            amount=subscription.plan.price,
            due_date=timezone.now() + timezone.timedelta(days=7)
        )

        return redirect('payment_success', invoice_id=invoice.id)

    return render(request, 'billing/renew.html', {'subscription': subscription})


@login_required
def update_plan(request, subscription_id):
    if request.method == 'POST':
        data = json.loads(request.body)

        subscription = get_object_or_404(UserSubscription, id=subscription_id)
        new_plan = get_object_or_404(SubscriptionPlan, id=data['plan_id'])

        subscription.plan = new_plan
        subscription.save()

        return JsonResponse({'success': True, 'message': 'Plan updated successfully'})


@login_required
def mark_invoice_paid(request, invoice_id):
    invoice = get_object_or_404(Invoice, id=invoice_id)
    invoice.status = 'paid'
    invoice.paid_date = timezone.now()
    invoice.save()

    return JsonResponse({'success': True, 'message': 'Invoice marked as paid'})


def raise_ticket(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        description = request.POST.get('description')
        category = request.POST.get('category')

        if subject and description and category:
            Ticket.objects.create(
                client=request.tenant,
                subject=subject,
                description=description,
                category=category
            )
            messages.success(request, "Your support ticket has been submitted successfully!")
            return redirect('raise_ticket')
        else:
            messages.error(request, "Please fill all fields before submitting.")

    return render(request, 'raise_ticket.html')