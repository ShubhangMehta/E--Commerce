from rest_framework.views import APIView
from rest_framework.response import Response
from inventory.services import StockUpdateService
from inventory.models import Product

class StockUpdateAPI(APIView):

    def post(self, request):
        product_id = request.data.get("product_id")
        quantity = request.data.get("quantity")

        product = Product.objects.get(id=product_id)
        service = StockUpdateService()

        updated_stock = service.update(product, quantity)

        return Response({
            "message": "Stock updated successfully",
            "product": product.name,
            "new_quantity": updated_stock.quantity
        })