from django.db.models import Q
from .product_base_service import ProductBaseService
from catalog.models import SingleProduct


class SingleProductService(ProductBaseService):
    model = SingleProduct

    def get_available_products(self, query=None):
        qs = (
            self.model.objects
            .filter(availability=True)
            .prefetch_related("images", "subcategory")
        )

        if query:
            qs = qs.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query) |
                Q(subcategory__name__icontains=query)
            )

        return qs
