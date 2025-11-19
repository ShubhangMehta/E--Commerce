# customers/apps.py
from django.apps import AppConfig

class CustomersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'customers'
    #verbose_name = 'Customers'

    def ready(self):
        # import signals so they get registered
        import customers.rzp_signals  # noqa
