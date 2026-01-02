from django.core.management.base import BaseCommand
from .models import ClientSubscription

class Command(BaseCommand):
    help = "Check subscription expiry and update status"

    def handle(self, *args, **kwargs):
        subs = ClientSubscription.objects.all()
        for sub in subs:
            sub.check_status()
        self.stdout.write(self.style.SUCCESS('Subscription status check complete'))
