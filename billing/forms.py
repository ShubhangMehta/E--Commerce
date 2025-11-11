from django import forms
from .models import PLAN_CHOICES, BILLING_INTERVALS

class CheckoutForm(forms.Form):
    desired_domain = forms.CharField(max_length=150)
    email = forms.EmailField()
    plan_name = forms.CharField()
