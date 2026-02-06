from django import forms
from django.forms.widgets import FileInput
from django.forms import inlineformset_factory

from .models import (
    SingleProduct,
    MultiProduct,
    SingleProductImage,
)

# ===============================
# Admin Multiple Upload Support
# ===============================

class MultipleFileInput(FileInput):
    allow_multiple_selected = True


class SingleProductAdminForm(forms.ModelForm):
    extra_images = forms.FileField(
        required=False,
        widget=MultipleFileInput(),
        help_text="You can upload multiple images at once"
    )

    class Meta:
        model = SingleProduct
        fields = "__all__"


class MultiProductAdminForm(forms.ModelForm):
    extra_images = forms.FileField(
        required=False,
        widget=MultipleFileInput(),
        help_text="You can upload multiple images at once"
    )

    class Meta:
        model = MultiProduct
        fields = "__all__"


# ===============================
# Dashboard CRUD Forms
# ===============================

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
