from django.contrib import admin
from .models import SingleProduct, SingleProductImage


class SingleProductImageInline(admin.TabularInline):
    model = SingleProductImage
    extra = 1
    fields = ("image", "image_type", "is_primary")


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
@admin.register(SingleProduct)
class SingleProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "brand_name",
        "price",
        "availability",
        "is_featured",
        "featured_order",
        "created_at",
        "refundable",
        "returnable",
    )

    list_filter = ("availability", "is_featured")
    search_fields = ("name", "brand_name")

    inlines = [SingleProductImageInline]


@admin.register(SingleProductImage)
class SingleProductImageAdmin(admin.ModelAdmin):
    list_display = ("product", "image_type", "is_primary", "created_at")
    list_filter = ("image_type", "is_primary")
