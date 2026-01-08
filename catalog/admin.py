# from django.contrib import admin
# from .models import (
#     SingleProduct,
#     SingleProductImage,
#     SubCategory,
#     MultiProduct, MultiProductImage,
#     MultiCategory, MultiSubCategory,
#     VariantType, VariantValue, MultiProductVariant
#     )


# @admin.register(SubCategory)
# class SubCategoryAdmin(admin.ModelAdmin):
#     search_fields = ("name",)


# class SingleProductImageInline(admin.TabularInline):
#     model = SingleProductImage
#     extra = 1


# @admin.register(SingleProduct)
# class SingleProductAdmin(admin.ModelAdmin):
#     list_display = ("name", "subcategory", "price", "availability")
#     list_filter = ("availability", "subcategory")
#     search_fields = ("name", "brand_name")
#     inlines = [SingleProductImageInline]

# #multi product

# @admin.register(MultiCategory)
# class MultiCategoryAdmin(admin.ModelAdmin):
#     search_fields = ("name",)


# @admin.register(MultiSubCategory)
# class MultiSubCategoryAdmin(admin.ModelAdmin):
#     list_filter = ("category",)


# class MultiProductImageInline(admin.TabularInline):
#     model = MultiProductImage
#     extra = 1


# class MultiProductVariantInline(admin.TabularInline):
#     model = MultiProductVariant
#     extra = 1


# @admin.register(MultiProduct)
# class MultiProductAdmin(admin.ModelAdmin):
#     list_display = ("name", "category", "availability")
#     list_filter = ("category", "subcategory", "availability")
#     inlines = [MultiProductImageInline, MultiProductVariantInline]


# admin.site.register(VariantType)
# admin.site.register(VariantValue)

from django.contrib import admin
from django.utils.html import format_html

from .models import (
    SingleProduct,
    SingleProductImage,
    SubCategory,

    MultiProduct,
    MultiProductImage,
    MultiCategory,
    MultiSubCategory,

    VariantType,
    VariantValue,
    MultiProductVariant
)

from .forms import (
    SingleProductAdminForm,
    MultiProductAdminForm
)

# ======================
# SINGLE PRODUCT ADMIN
# ======================

@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


class SingleProductImageInline(admin.TabularInline):
    model = SingleProductImage
    extra = 0
    readonly_fields = ("preview",)
    fields = ("preview", "image", "is_primary")

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:80px;" />',
                obj.image.url
            )
        return "-"


@admin.register(SingleProduct)
class SingleProductAdmin(admin.ModelAdmin):
    form = SingleProductAdminForm
    list_display = ("name", "subcategory", "price", "availability")
    list_filter = ("availability", "subcategory")
    search_fields = ("name", "brand_name")
    inlines = [SingleProductImageInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        images = request.FILES.getlist("extra_images")
        for img in images:
            SingleProductImage.objects.create(
                product=obj,
                image=img
            )

# ======================
# MULTI PRODUCT ADMIN
# ======================

@admin.register(MultiCategory)
class MultiCategoryAdmin(admin.ModelAdmin):
    search_fields = ("name",)


@admin.register(MultiSubCategory)
class MultiSubCategoryAdmin(admin.ModelAdmin):
    list_filter = ("category",)


class MultiProductImageInline(admin.TabularInline):
    model = MultiProductImage
    extra = 0
    readonly_fields = ("preview",)
    fields = ("preview", "image", "is_primary")

    def preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width:80px;" />',
                obj.image.url
            )
        return "-"


class MultiProductVariantInline(admin.TabularInline):
    model = MultiProductVariant
    extra = 1


@admin.register(MultiProduct)
class MultiProductAdmin(admin.ModelAdmin):
    form = MultiProductAdminForm
    list_display = ("name", "category", "availability")
    list_filter = ("category", "subcategory", "availability")
    inlines = [MultiProductImageInline, MultiProductVariantInline]

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)

        images = request.FILES.getlist("extra_images")
        for img in images:
            MultiProductImage.objects.create(
                product=obj,
                image=img
            )


# ======================
# VARIANTS
# ======================

admin.site.register(VariantType)
admin.site.register(VariantValue)
