from django.db import models
from django_tenants.models import TenantMixin, DomainMixin

# Create your models here.

class Client(TenantMixin):
    name = models.CharField(max_length=100)
    #schema_name = models.CharField(max_length=63, unique=True)
    paid_until = models.DateField(null=True, blank=True)
    on_trial = models.BooleanField(default=True)
    created_on = models.DateField(auto_now_add=True)
    owner_name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    company = models.CharField(max_length=200, blank=True, null=True)
    Address = models.TextField(max_length=200, blank=True, null=True)

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = True

class Domain(DomainMixin):
    
    def __str__(self):
        return self.domain