# customers/apps.py

"""
App Configuration for the 'customers' Django App
------------------------------------------------

This module defines the configuration class for the app
and ensures that all signals are imported when the app is ready.
"""

from django.apps import AppConfig

class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'
