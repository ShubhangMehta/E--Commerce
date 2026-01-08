from django import forms
from django.forms.widgets import FileInput
from .models import SingleProduct, MultiProduct


# ✅ Custom widget that supports multiple files (Django 5.x safe)
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
