from django.core.management.base import BaseCommand
from django.utils import timezone
from billing.models import Subscription

class Command(BaseCommand):
    help = "Mark subscriptions expired when end date passed"

    def handle(self, *args, **opts):
        now = timezone.now()
        qs = Subscription.objects.filter(status="active", current_period_end__lt=now)
        count = 0
        for s in qs:
            s.status = "past_due"
            s.save(update_fields=["status"])
            count += 1
        self.stdout.write(self.style.SUCCESS(f"Marked past_due: {count}"))
