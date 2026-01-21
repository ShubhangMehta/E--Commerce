import os
import sys
import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core_app.settings")
django.setup()


from django_tenants.utils import schema_context
from customers.models import Client
from orders.models import Order
import json

tenant = Client.objects.get(schema_name="geforce")

with schema_context(tenant.schema_name):
    data = list(Order.objects.all().values())

json_data = json.dumps(data, indent=2)
print(json_data)