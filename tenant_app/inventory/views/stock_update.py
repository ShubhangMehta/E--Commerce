from rest_framework.views import APIView
from rest_framework.response import Response
from tenant_app.inventory.services.stock_update_service import StockUpdateService
from tenant_app.inventory.models import Product

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
