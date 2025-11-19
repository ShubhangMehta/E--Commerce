# customers/rzp_signals.py
import threading
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import RzpSubscription, RzpPlan, Client

_state = threading.local()

def _enter(flag_name):
    if not hasattr(_state, flag_name):
        setattr(_state, flag_name, 0)
    setattr(_state, flag_name, getattr(_state, flag_name) + 1)

def _leave(flag_name):
    setattr(_state, flag_name, max(getattr(_state, flag_name, 1) - 1, 0))

def _is_inside(flag_name):
    return getattr(_state, flag_name, 0) > 0


def _safe_make_aware(dt):
    if dt is None:
        return None
    if timezone.is_aware(dt):
        return dt
    if isinstance(dt, datetime):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    # if it's a date, set start of day
    return timezone.make_aware(datetime.combine(dt, datetime.min.time()), timezone.get_current_timezone())


# =========================
# Subscription -> Client
# =========================
@receiver(post_save, sender=Subscription)
def subscription_updates_client(sender, instance: Subscription, created, **kwargs):
    """
    Keep Client fields in sync whenever a Subscription becomes active or its period changes.
    """
    if _is_inside("client_to_sub"):
        # currently handling Client -> Subscription; don't bounce back
        return

    if not instance.client:
        return

    if instance.status != "active" or not instance.current_period_end:
        # Only sync dates when sub is active with a defined period
        return

    try:
        _enter("sub_to_client")
        client = instance.client

        # Sync subscription period into client for enforcement middleware
        changed = False
        # subscription_start
        start_date = (instance.started_at.date() if instance.started_at else timezone.now().date())
        if not client.subscription_start:
            client.subscription_start = start_date
            changed = True

        # subscription_end
        end_date = instance.current_period_end.date()
        if client.subscription_end != end_date:
            client.subscription_end = end_date
            changed = True

        # plan type (store the plan name)
        if getattr(client, "plan_type", None) != instance.plan.name:
            client.plan_type = instance.plan.name
            changed = True

        if changed:
            client.save(update_fields=["subscription_start", "subscription_end", "plan_type"])
    finally:
        _leave("sub_to_client")


# =========================
# Client -> Subscription
# =========================
@receiver(post_save, sender=Client)
def client_updates_subscription(sender, instance: Client, created, **kwargs):
    """
    If admin edits Client (plan_type, subscription_start/end, status), update the latest Subscription.
    """
    if _is_inside("sub_to_client"):
        # currently handling Subscription -> Client; don't bounce back
        return

    # Find most relevant subscription for this client
    sub = (Subscription.objects
           .filter(client=instance)
           .order_by("-started_at", "-id")
           .first())
    if not sub:
        return

    try:
        _enter("client_to_sub")

        # Plan sync: try to match Plan by name and keep existing interval if names match
        target_plan = None
        if getattr(instance, "plan_type", None):
            # prefer a plan with same name and same interval as current subscription, otherwise fallback to any name match
            target_plan = (Plan.objects.filter(name=instance.plan_type, interval=sub.plan.interval).first()
                           or Plan.objects.filter(name=instance.plan_type).first())

        if target_plan and sub.plan_id != target_plan.id:
            sub.plan = target_plan

        # Dates sync
        # started_at: prefer client's subscription_start
        if instance.subscription_start:
            sub.started_at = _safe_make_aware(datetime.combine(instance.subscription_start, datetime.min.time()))
        # current_period_end: prefer client's subscription_end
        if instance.subscription_end:
            sub.current_period_end = _safe_make_aware(datetime.combine(instance.subscription_end, datetime.min.time()))

        # current_period_start: keep sane when started_at is set and start is empty
        if not sub.current_period_start and sub.started_at:
            sub.current_period_start = sub.started_at

        # status sync (basic mapping): if client is Active, subscription should be at least 'active'
        # If you use more granular status on Client, map here accordingly.
        if instance.status == "Active" and sub.status != "active":
            sub.status = "active"
        elif instance.status == "Suspended" and sub.status not in ("cancelled", "expired"):
            sub.status = "past_due"  # or keep as-is; adjust to your needs

        sub.save()
    finally:
        _leave("client_to_sub")