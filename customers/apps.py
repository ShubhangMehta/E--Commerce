# customers/apps.py

"""
App Configuration for the 'customers' Django App
------------------------------------------------

This module defines the configuration class for the app
and ensures that all signals are imported when the app is ready.
"""

from django.apps import AppConfig


class CustomersConfig(AppConfig):
    """
    Configuration class for the Customers app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'
    # verbose_name = 'Customers'   # Optional display name for admin panel

    def ready(self):
        # Import signals so they get registered
        import customers.rzp_signals  # noqa: F401


class BillingConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'billing'
    verbose_name = 'Billing & Subscriptions'

    def ready(self):
        # Import signal handlers so Django registers them
        pass  # noqa: F401