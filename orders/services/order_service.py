from django.db import transaction
from django.db.models import F

from orders.models import Order, OrderItem
from users.models import Coordinate

from .pricing_service import PricingService

class OrderService:
    """
    Central order engine.

    Responsibilities:
    - validate checkout inputs
    - convert cart items into Order + OrderItems
    - preserve shipping snapshot on Order
    - customer and tenant order queries
    """

    @staticmethod
    def _tenant_value(tenant):
        """
        Supports either:
        - tenant object with .schema_name
        - raw tenant string already stored in Order.tenant
        """
        return getattr(tenant, "schema_name", tenant)

    @staticmethod
    def _get_address(*, subject, address_id):
        return Coordinate.objects.get(
            id=address_id,
            user=subject,
        )

    @staticmethod
    def _build_shipping_address(address):
        parts = [
            address.address_type,
            address.address_line1,
            address.address_line2,
            address.landmark,
            address.city,
            address.state,
            address.postal_code,
            address.country,
        ]
        return ", ".join(part.strip() for part in parts if part and part.strip())

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
        Convert cart_items into:
        - Order
        - OrderItem rows
        """
        if not subject:
            raise ValueError("Subject is required to create an order.")

        if not cart_items:
            raise ValueError("Cannot create an order from an empty cart.")

        address = OrderService._get_address(subject=subject, address_id=address_id)
        totals = PricingService.calculate_from_items(items=cart_items, coupon=coupon)

        order = Order.objects.create(
            tenant=OrderService._tenant_value(tenant),
            subject=subject,
            customer_email=subject.email or address.email or "",
            customer_name=subject.full_name or address.full_name or "",
            
            coupon=totals["coupon"],

            shipping_full_name=address.full_name,
            shipping_phone=address.phone,
            shipping_address_type=address.address_type,
            shipping_address=OrderService._build_shipping_address(address),
            shipping_city=address.city,
            shipping_state=address.state,
            shipping_postal_code=address.postal_code,
            shipping_country=address.country,

            subtotal_amount=totals["subtotal"],
            shipping_amount=totals["shipping_amount"],
            discount_amount=totals["discount_amount"],
            total_amount=totals["total_amount"],
        )

        OrderService._create_order_items(order=order, cart_items=cart_items)

        if totals["coupon"]:
            type(totals["coupon"]).objects.filter(id=totals["coupon"].id).update(
                used_count=F("used_count") + 1
            )

        return order

    @staticmethod
    def _create_order_items(*, order, cart_items):
        order_items = []

        for item in cart_items:
            product = item["product"]

            order_items.append(
                OrderItem(
                    order=order,
                    product=product,
                    product_name_snapshot=product.name,
                    product_price_snapshot=product.price,
                    quantity=item["quantity"],
                    line_total=item["line_total"],
                )
            )

        OrderItem.objects.bulk_create(order_items)

    @staticmethod
    def get_customer_orders(*, subject):
        return (
            Order.objects
            .filter(subject=subject)
            .select_related("subject", "coordinate", "coupon")
            .order_by("-created_at")
        )

    @staticmethod
    def get_customer_order_detail(*, subject, order_id):
        return (
            Order.objects
            .filter(subject=subject, id=order_id)
            .select_related("subject", "coordinate", "coupon")
            .prefetch_related("items__product")
            .get()
        )

    @staticmethod
    def get_tenant_orders(*, tenant):
        return (
            Order.objects
            .filter(tenant=OrderService._tenant_value(tenant))
            .select_related("subject", "coordinate", "coupon")
            .order_by("-created_at")
        )

    @staticmethod
    def update_status(*, order, new_status):
        order.status = new_status
        order.save(update_fields=["status"])
        return order