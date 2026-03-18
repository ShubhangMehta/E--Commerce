from django.db import transaction
from orders.models import Order, OrderItem,Coupon
from users.models import Coordinate
from decimal import Decimal
from django.db.models import F



class OrderService:
    """
    CENTRAL ORDER ENGINE
    --------------------
    Converts cart → Order → OrderItems
    Handles customer + tenant queries.
    """

    # =========================================================
    # 🛒 CHECKOUT ENGINE (MAIN FUNCTION)
    # =========================================================
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(
        
        *,
        tenant,
        subject,
        cart_items,
        address_id,
        coupon=None,
        
    ):
        """
        Convert session cart → DB Order + OrderItems
        """

        # 1️⃣ Validate & fetch shipping address
        address = Coordinate.objects.get(
            id=address_id,
            user=subject
        )

        totals = OrderService._calculate_totals(cart_items)

        subtotal = totals["subtotal"]
        discount = Decimal("0")

        if coupon and coupon.is_valid(subtotal):
        
            discount = (subtotal * coupon.discount_percent) / Decimal("100")

            if coupon.max_discount:
                discount = min(discount, coupon.max_discount)

        else:
            coupon = None

        final_total = max(totals["grand_total"] - discount, 0)

        order = Order.objects.create(
            tenant=tenant,
            subject=subject,
            total_amount=final_total,
            coupon=coupon,
            discount_amount=discount,

            shipping_full_name=address.full_name,
            shipping_phone=address.phone,
            shipping_house_no=address.house_no,
            shipping_landmark=address.landmark,
            shipping_address=address.address,  # fix this field
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
        )

        OrderService._create_order_items(order, cart_items)

        if coupon:
            Coupon.objects.filter(id=coupon.id).update(
                used_count=F("used_count") + 1
            )
        return order

    # =========================================================
    # 💰 CALCULATIONS
    # =========================================================
    @staticmethod
    def _calculate_totals(cart_items):
        """
        Cart items come from theme helper:
        {
            "product": product,
            "quantity": qty,
            "line_total": price * qty
        }
        """
        subtotal = sum(item["line_total"] for item in cart_items)

        shipping = 0      # future feature
        tax = 0           # future feature

        grand_total = subtotal + shipping + tax

        return {
            "subtotal": subtotal,
            "shipping": shipping,
            "tax": tax,
            "grand_total": grand_total,
        }

    # =========================================================
    # 📦 CREATE ORDER ITEMS
    # =========================================================
    @staticmethod
    def _create_order_items(order, cart_items):
        order_items = []

        for item in cart_items:
            product = item["product"]

            order_items.append(
                OrderItem(
                    order=order,

                    # ✅ direct FK now
                    product=product,

                    # snapshot
                    product_name=product.name,
                    product_price=product.price,

                    quantity=item["quantity"],
                    line_total=item["line_total"],
                )
            )

        OrderItem.objects.bulk_create(order_items)

       
    # =========================================================
    # 👤 CUSTOMER QUERIES
    # =========================================================
    @staticmethod
    def get_customer_orders(*, subject):
        """
        Used in storefront "My Orders" page
        """
        return (
            Order.objects
            .filter(subject=subject)
            .select_related("tenant")
            .order_by("-created_at")
        )

    @staticmethod
    def get_customer_order_detail(*, subject, order_id):
        """
        Used in order detail page
        Security: user can only see their own order
        """
        order = (
            Order.objects
            .select_related("tenant")
            .prefetch_related("items__product")
            .get(id=order_id, subject=subject)
        )
        return order

    # =========================================================
    # 🏪 TENANT (ADMIN DASHBOARD)
    # =========================================================
    @staticmethod
    def get_tenant_orders(*, tenant):
        """
        Used in tenant dashboard → Orders list
        """
        return (
            Order.objects
            .filter(tenant=tenant)
            .select_related("subject")
            .order_by("-created_at")
        )

    # =========================================================
    # 🔄 ORDER STATUS UPDATE
    # =========================================================
    @staticmethod
    def update_status(*, order, new_status):
        order.status = new_status
        order.save(update_fields=["status"])
        return order
