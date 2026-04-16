from django import forms
from .models import Coupon

class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon
        fields = [
            "code",
            "discount_percent",
            "max_discount",
            "min_order_value",
            "valid_from",
            "valid_to",
            "usage_limit",
            "active",
        ]

        widgets = {
            "valid_from": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "valid_to": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }