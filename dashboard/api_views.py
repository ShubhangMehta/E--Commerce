from django.http import JsonResponse
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
from catalog.models import SingleProduct
from orders.models import OrderItem


def monthly_top_products(request):

    product_content_type = ContentType.objects.get_for_model(SingleProduct)

    top_products = (
        OrderItem.objects
<<<<<<< HEAD
        .filter(content_type=product_content_type)
        .values("product_name")
=======
        .filter(
            order__created_at__gte=last_month,
            content_type=product_content_type   # 🔥 KEY FIX
        )
        .values("product_name_snapshot")  # 🔥 KEY FIX
>>>>>>> origin/Humera
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )

<<<<<<< HEAD
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
=======
    labels = [p["product_name_snapshot"] for p in top_products]
    data = [p["total_sold"] for p in top_products]
>>>>>>> origin/Humera

    return JsonResponse({
        "labels": labels,
        "data": data,
        "percentages": percentages
    })