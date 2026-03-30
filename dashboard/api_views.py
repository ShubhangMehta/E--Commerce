from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from catalog.models import SingleProduct
from orders.models import OrderItem


def monthly_top_products(request):

    product_content_type = ContentType.objects.get_for_model(SingleProduct)

    top_products = (
        OrderItem.objects
        .filter(content_type=product_content_type)
        .values("product_name")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

    labels = []
    data = []

    for p in top_products:
        labels.append(p["product_name"])
        data.append(p["total_sold"] or 0)

    total = sum(data)

    percentages = [
        round((v / total) * 100, 1) if total > 0 else 0
        for v in data
    ]

    return JsonResponse({
        "labels": labels,
        "data": data,
        "percentages": percentages
    })