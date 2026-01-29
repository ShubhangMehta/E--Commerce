from django import forms
from .models import SingleProduct

class SingleProductForm(forms.ModelForm):
    class Meta:
        model = SingleProduct
        fields = [
            "brand_name",
            "name",
            "price",
            "description",
            "availability",
            "seller",
            "estimated_delivery",
            "refundable",
            "returnable",
        ]
