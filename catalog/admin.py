from django.contrib import admin
from .models import SingleProduct, SingleProductImage


class SingleProductImageInline(admin.TabularInline):
    model = SingleProductImage
    extra = 1
    fields = ("image", "is_primary")


# @admin.register(SingleProduct)
# class SingleProductAdmin(admin.ModelAdmin):
#     list_display = (
#         "name",
#         "brand_name",
#         "price",
#         "availability",
#         "seller",
#         "refundable",
#         "returnable",
#     )
#     list_filter = ("availability", "refundable", "returnable")
#     search_fields = ("name", "brand_name")
#     inlines = [SingleProductImageInline]
