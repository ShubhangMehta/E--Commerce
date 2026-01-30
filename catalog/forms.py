from django import forms
from django.forms import inlineformset_factory
from .models import SingleProduct , SingleProductImage

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

class SingleProductImageForm(forms.ModelForm):
    class Meta:
        model = SingleProductImage
        fields = ["image", "is_primary"]

ProductImageFormSet = inlineformset_factory(
    SingleProduct,
    SingleProductImage,
    form=SingleProductImageForm,
    extra=3,
    can_delete=True
)