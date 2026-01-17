# customers/logging_filters.py
import logging
from django.db import connection

class TenantSchemaFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        # connection.schema_name is set by django-tenants when request switches schema
        record.schema_name = getattr(connection, "schema_name", "unknown")
        return True
