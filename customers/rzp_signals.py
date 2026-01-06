# customers/rzp_signals.py

"""
Razorpay Signal Handlers
------------------------

This module keeps Client and RzpSubscription objects in sync.
Sync Direction:
    - Subscription ➜ Client
    - Client ➜ Subscription

The syncing is protected using thread-local flags to prevent circular updates.
"""

import threading
from datetime import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

#from .models import RzpSubscription, RzpPlan, Client
from .models import ClientSubscription, Client


# ============================================================================
# Thread-local protection flags (prevent infinite recursion)
# ============================================================================

_state = threading.local()

def _enter(flag_name):
    """Increment a thread-local counter for the given flag."""
    setattr(_state, flag_name, getattr(_state, flag_name, 0) + 1)

def _leave(flag_name):
    """Decrement the flag counter (but never below zero)."""
    setattr(_state, flag_name, max(getattr(_state, flag_name, 1) - 1, 0))

def _is_inside(flag_name):
    """Returns True if the code is already executing inside this flag."""
    return getattr(_state, flag_name, 0) > 0


# ============================================================================
# Datetime Handling Helper
# ============================================================================

def _safe_make_aware(dt):
    """
    Ensures the given datetime or date object is timezone-aware.

    Allowed:
        - timezone-aware datetime   (returned unchanged)
        - naive datetime            (converted to aware)
        - date                      (converted to datetime at start of day)
    """
    if dt is None:
        return None

    if timezone.is_aware(dt):
        return dt

    if isinstance(dt, datetime):
        return timezone.make_aware(dt, timezone.get_current_timezone())

    # If dt is a date, convert to datetime at midnight
    dt_full = datetime.combine(dt, datetime.min.time())
    return timezone.make_aware(dt_full, timezone.get_current_timezone())


# ============================================================================
# Subscription → Client Sync
# ============================================================================

@receiver(post_save, sender=ClientSubscription)
def subscription_updates_client(sender, instance: ClientSubscription, created, **kwargs):
    """
    Sync Client fields whenever a subscription becomes active or its period changes.

    Conditions:
        - Only runs if subscription is "active"
        - Updates client's:
              * subscription_start
              * subscription_end
              * plan_type
    """
    # Prevent circular update bounce-back
    if _is_inside("client_to_sub"):
        return

    # Subscription must belong to a client
    if not instance.client:
        return

    # Only sync when active + period end exists
    if instance.status != "active" or not instance.current_period_end:
        return

    try:
        _enter("sub_to_client")

        client = instance.client
        changed = False

        # -----------------------------------------------
        # Sync subscription start date
        # -----------------------------------------------
        start_date = (
            instance.started_at.date() 
            if instance.started_at 
            else timezone.now().date()
        )

        if not client.subscription_start:
            client.subscription_start = start_date
            changed = True

        # -----------------------------------------------
        # Sync subscription end date
        # -----------------------------------------------
        end_date = instance.current_period_end.date()

        if client.subscription_end != end_date:
            client.subscription_end = end_date
            changed = True

        # -----------------------------------------------
        # Sync plan type
        # -----------------------------------------------
        if getattr(client, "plan_type", None) != instance.plan.name:
            client.plan_type = instance.plan.name
            changed = True

        # Save only if needed
        if changed:
            client.save(update_fields=["subscription_start", "subscription_end", "plan_type"])

    finally:
        _leave("sub_to_client")


# ============================================================================
# Client → Subscription Sync
# ============================================================================

@receiver(post_save, sender=Client)
def client_updates_subscription(sender, instance: Client, created, **kwargs):
    """
    Sync Subscription fields when Admin edits Client details.

    Syncs:
        - Plan type → subscription.plan
        - subscription_start → subscription.started_at
        - subscription_end → subscription.current_period_end
        - status (Active / Suspended)

    Only updates the latest subscription for that client.
    """
    # Prevent circular update bounce-back
    if _is_inside("sub_to_client"):
        return

    # Fetch the most recent subscription for this client
    sub = (
        ClientSubscription.objects
        .filter(client=instance)
        .order_by("-started_at", "-id")
        .first()
    )

    if not sub:
        return

    try:
        _enter("client_to_sub")

        # --------------------------------------------------
        # PLAN SYNC
        # --------------------------------------------------
        target_plan = None

        if getattr(instance, "plan_type", None):
            # Prefer same plan name + same interval first
            target_plan = (
                RzpPlan.objects.filter(
                    name=instance.plan_type,
                    interval=sub.plan.interval
                ).first()
                or 
                RzpPlan.objects.filter(
                    name=instance.plan_type
                ).first()
            )

        if target_plan and sub.plan_id != target_plan.id:
            sub.plan = target_plan

        # --------------------------------------------------
        # DATE SYNC
        # --------------------------------------------------
        if instance.subscription_start:
            sub.started_at = _safe_make_aware(
                datetime.combine(instance.subscription_start, datetime.min.time())
            )

        if instance.subscription_end:
            sub.current_period_end = _safe_make_aware(
                datetime.combine(instance.subscription_end, datetime.min.time())
            )

        if not sub.current_period_start and sub.started_at:
            sub.current_period_start = sub.started_at

        # --------------------------------------------------
        # STATUS SYNC
        # --------------------------------------------------
        if instance.status == "Active" and sub.status != "active":
            sub.status = "active"

        elif instance.status == "Suspended" and sub.status not in ("cancelled", "expired"):
            sub.status = "past_due"   # adjust to your business rules

        # Save subscription
        sub.save()

    finally:
        _leave("client_to_sub")
