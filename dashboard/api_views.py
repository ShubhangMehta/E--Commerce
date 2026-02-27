from django.http import JsonResponse
from django.utils import timezone
from datetime import timedelta
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType

from orders.models import OrderItem
from catalog.models import SingleProduct


def monthly_top_products(request):
    # last 30 days
    last_month = timezone.now() - timedelta(days=30)

    # ⭐ VERY IMPORTANT — get content type of SingleProduct
    product_content_type = ContentType.objects.get_for_model(SingleProduct)

    # get top sold products
    top_products = (
        OrderItem.objects
        .filter(
            order__created_at__gte=last_month,
            content_type=product_content_type   # 🔥 KEY FIX
        )
        .values("product_name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    labels = [p["product_name"] for p in top_products]
    data = [p["total_sold"] for p in top_products]

    return JsonResponse({
        "labels": labels,
        "data": data,
    })
