from django.http import HttpResponse
from django.db import connection

def test_view(request):
    current_schema = connection.schema_name
    return HttpResponse(f"You are connected to demo schema: {current_schema}")

