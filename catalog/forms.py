from django import forms
from django.forms import inlineformset_factory
from .models import (
    SingleProduct,
    SingleProductImage,
    Category,
    SubCategory
)


# PRODUCT FORM
class SingleProductForm(forms.ModelForm):
    class Meta:
        model = SingleProduct
        fields = [
            "brand_name",
            "name",
            "category",
            "sub_category",
            "price",
            "description",
            "availability",
            "seller",
            "estimated_delivery",
            "refundable",
            "returnable",
            "is_featured",
            "featured_order",
        ]


# CATEGORY FORM
class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ["name"]


# SUBCATEGORY FORM
class SubCategoryForm(forms.ModelForm):
    class Meta:
        model = SubCategory
        fields = ["category", "name"]


# PRODUCT IMAGE FORM
class SingleProductImageForm(forms.ModelForm):
    class Meta:
        model = SingleProductImage
        fields = ["image", "image_type", "is_primary"]


# IMAGE FORMSET
ProductImageFormSet = inlineformset_factory(
    SingleProduct,
    SingleProductImage,
    form=SingleProductImageForm,
    extra=3,
    can_delete=True
)


# BANNER FORM
class BannerForm(forms.ModelForm):
    class Meta:
        model = SingleProductImage
        fields = ["image"]