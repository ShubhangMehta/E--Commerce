# from .product_base_service import ProductBaseService
# from catalog.models import SingleProduct


# class SingleProductService(ProductBaseService):
#     model = SingleProduct

#     def get_available_products(self):
#         return self.model.objects.filter(availability=True)

from .product_base_service import ProductBaseService
from catalog.models import SingleProduct


class SingleProductService(ProductBaseService):
    model = SingleProduct

    def get_available_products(self):
        return (
            self.model.objects
            .filter(availability=True)
            .prefetch_related("images")
        )