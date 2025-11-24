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

    Attributes:
        default_auto_field: Specifies the default type of primary key fields.
        name: The full Python path to the app.
    """

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'
    # verbose_name = 'Customers'   # Optional display name for admin panel

    def ready(self):
        """
        Executed when the Django app is fully initialized.

        This method ensures that the signal handlers in rzp_signals.py
        are loaded so that they register properly with Django's signal framework.
        """
        # Import signal handlers so Django registers them
        import customers.rzp_signals  # noqa: F401 (import unused intentionally)
