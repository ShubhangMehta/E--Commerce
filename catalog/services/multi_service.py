from django.db.models import Q
from catalog.models import MultiProduct


class MultiProductService:
    def get_products(self, query=None, category_id=None):
        qs = (
            MultiProduct.objects
            .filter(availability=True)
            .prefetch_related("images", "variants", "category", "subcategory")
        )

        # 🔍 Search
        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(category__name__icontains=query) |
                Q(subcategory__name__icontains=query)
            )

        # 🗂 Category filter
        if category_id:
            qs = qs.filter(category_id=category_id)

        return qs

