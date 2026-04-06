from decimal import Decimal
from catalog.models import SingleProduct

class CartService:
    """
    Owns the session cart only.

    Session format:
        session["cart"] = {
            "<product_id>": {
                "qty": int
            }
        }

        session["selected_address_id"] = <int>
        session["coupon_code"] = "SAVE10"
    """

    SESSION_KEY = "cart"
    ADDRESS_KEY = "selected_address_id"
    COUPON_KEY = "coupon_code"

    @staticmethod
    def get_cart(session) -> dict:
        return session.get(CartService.SESSION_KEY, {})

    @staticmethod
    def set_cart(session, cart: dict) -> None:
        session[CartService.SESSION_KEY] = cart
        session.modified = True

    @staticmethod
    def add(session, product_id: int, qty: int = 1) -> None:
        cart = CartService.get_cart(session)
        pid = str(product_id)

        cart.setdefault(pid, {"qty": 0})
        cart[pid]["qty"] = int(cart[pid]["qty"]) + max(1, int(qty))

        CartService.set_cart(session, cart)

    @staticmethod
    def update(session, product_id: int, qty: int) -> None:
        cart = CartService.get_cart(session)
        pid = str(product_id)
        qty = int(qty)

        if pid not in cart:
            return

        if qty <= 0:
            cart.pop(pid, None)
        else:
            cart[pid]["qty"] = qty

        CartService.set_cart(session, cart)

    @staticmethod
    def remove(session, product_id: int) -> None:
        cart = CartService.get_cart(session)
        cart.pop(str(product_id), None)
        CartService.set_cart(session, cart)

    @staticmethod
    def clear(session) -> None:
        session.pop(CartService.SESSION_KEY, None)
        session.pop(CartService.ADDRESS_KEY, None)
        session.pop(CartService.COUPON_KEY, None)
        session.modified = True

    @staticmethod
    def build_items(session):
        """
        Returns normalized cart items:

        [
            {
                "product": <SingleProduct>,
                "quantity": 2,
                "unit_price": Decimal("100.00"),
                "line_total": Decimal("200.00"),
            }
        ]
        """
        cart = CartService.get_cart(session)
        if not cart:
            return []

        product_ids = [int(pid) for pid in cart.keys()]
        products = {
            product.id: product
            for product in SingleProduct.objects.filter(id__in=product_ids)
        }

        items = []

        for pid_str, data in cart.items():
            product = products.get(int(pid_str))
            if not product:
                continue

            quantity = max(1, int(data.get("qty", 1)))
            unit_price = Decimal(str(product.price or "0.00"))
            line_total = unit_price * quantity

            items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
            )

        return items

    @staticmethod
    def get_subtotal(items) -> Decimal:
        return sum((item["line_total"] for item in items), start=Decimal("0.00"))

    @staticmethod
    def set_selected_address(session, address_id: int) -> None:
        session[CartService.ADDRESS_KEY] = int(address_id)
        session.modified = True

    @staticmethod
    def get_selected_address_id(session):
        return session.get(CartService.ADDRESS_KEY)

    @staticmethod
    def set_coupon(session, code: str) -> None:
        code = (code or "").strip()

        if code:
            session[CartService.COUPON_KEY] = code
        else:
            session.pop(CartService.COUPON_KEY, None)

        session.modified = True

    @staticmethod
    def get_coupon_code(session) -> str:
        return (session.get(CartService.COUPON_KEY) or "").strip()