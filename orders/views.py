# from django.shortcuts import render, redirect

# # Dummy products (like catalog)
# PRODUCTS = [
#     {"id": 1, "name": "Laptop", "price": 50000},
#     {"id": 2, "name": "Mouse", "price": 500},
#     {"id": 3, "name": "Keyboard", "price": 1500},
# ]

# # Dummy orders list
# ORDERS = []


# def order_create(request):
#     # Initialize cart
#     if "cart" not in request.session:
#         request.session["cart"] = []

#     cart = request.session["cart"]

#     # ADD TO CART
#     if request.method == "POST" and "product_id" in request.POST:
#         product_id = int(request.POST.get("product_id"))
#         product = next(p for p in PRODUCTS if p["id"] == product_id)

#         cart.append(product)
#         request.session["cart"] = cart
#         return redirect("order_create")

#     total = sum(item["price"] for item in cart)

#     return render(
#         request,
#         "orders/customer/order_create.html",
#         {
#             "products": PRODUCTS,
#             "cart": cart,
#             "total": total,
#         }
#     )


# def remove_from_cart(request, index):
#     cart = request.session.get("cart", [])

#     if 0 <= index < len(cart):
#         cart.pop(index)

#     request.session["cart"] = cart
#     return redirect("order_create")


# def place_order(request):
#     cart = request.session.get("cart", [])

#     if not cart:
#         return redirect("order_create")

#     total = sum(item["price"] for item in cart)

#     # Create order
#     ORDERS.append({
#         "id": len(ORDERS) + 1,
#         "items": cart,
#         "total": total,
#         "status": "Placed",
#     })

#     # Clear cart
#     request.session["cart"] = []

#     return redirect("order_list")


# def order_list(request):
#     return render(
#         request,
#         "orders/customer/order_list.html",
#         {"orders": ORDERS}
#     )



# # order list 
# from django.shortcuts import render

# def order_list(request):
#     # Backend data (later this will come from DB)
#     orders = [
#         {
#             "order_id": "ORD001",
#             "status": "Pending",
#             "total": 2500,
#         },
#         {
#             "order_id": "ORD002",
#             "status": "Delivered",
#             "total": 1800,
#         },
#     ]

#     return render(
#         request,
#         "orders/customer/order_list.html",
#         {"orders": orders}
#     )


# # invoice section

# from django.shortcuts import render

# def invoice_view(request, order_id):
#     # Backend dummy data (later comes from DB)
#     invoice_data = {
#         "order_id": order_id,
#         "customer": "Onkar Shinde",
#         "items": [
#             {"name": "Laptop", "price": 50000},
#             {"name": "Mouse", "price": 500},
#         ],
#         "total": 50500,
#         "status": "Paid",
#     }

#     return render(
#         request,
#         "orders/customer/invoice.html",
#         {"invoice": invoice_data}
#     )
 



from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa  
from io import BytesIO
from .models import Order


def order_list(request):
    orders = Order.objects.all().order_by("-created_at")
    return render(
        request,
        "orders/customer/order_list.html",
        {"orders": orders}
    )



def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/customer/order_detail.html", {"order": order})


def order_create(request):
    if request.method == "POST":
        Order.objects.create(
            user=request.user,
            order_number=request.POST["order_number"],
            total_amount=request.POST["total_amount"],
        )
        return redirect("order_list")

    return render(request, "orders/customer/order_create.html")


def invoice_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "orders/customer/invoice.html", {"order": order})


def invoice_pdf(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    template = get_template("orders/customer/invoice.html")
    html = template.render({"order": order})

    result = BytesIO()
    pdf = pisa.CreatePDF(html, dest=result)

    if pdf.err:
        return HttpResponse("Error generating PDF")

    response = HttpResponse(result.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="invoice_{order.order_number}.pdf"'
    )
    return response
