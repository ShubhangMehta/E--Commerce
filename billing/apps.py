# billing/apps.py
from django.apps import AppConfig

class BillingConfig(AppConfig):
    name = "billing"
    verbose_name = "Billing"

    def ready(self):
        # Register signal handlers
        from . import signals  # noqa

