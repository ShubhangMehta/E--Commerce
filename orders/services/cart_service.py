from decimal import Decimal
from catalog.models import SingleProduct

class CartService:
    """
    Owns session cart: add/update/remove + building cart_items for OrderService.
    Session format:
      session["cart"] = { "<product_id>": {"qty": int} }
      session["selected_address_id"] = "<id>"
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
        cart[pid]["qty"] = int(cart[pid]["qty"]) + int(qty)
        CartService.set_cart(session, cart)

    @staticmethod
    def update(session, product_id: int, qty: int) -> None:
        cart = CartService.get_cart(session)
        pid = str(product_id)
        if pid in cart:
            cart[pid]["qty"] = max(1, int(qty))
            CartService.set_cart(session, cart)

    @staticmethod
    def remove(session, product_id: int) -> None:
        cart = CartService.get_cart(session)
        cart.pop(str(product_id), None)
        CartService.set_cart(session, cart)

    @staticmethod
    def clear(session) -> None:
        CartService.set_cart(session, {})

    @staticmethod
    def items_and_totals(session):
        """
        Returns: (cart_items, subtotal, total)
        cart_items is compatible with OrderService._calculate_totals() expectation. :contentReference[oaicite:7]{index=7}
        """
        cart = CartService.get_cart(session)
        product_ids = [int(pid) for pid in cart.keys()] if cart else []
        products = {p.id: p for p in SingleProduct.objects.filter(id__in=product_ids)}

        items = []
        subtotal = Decimal("0")

        for pid_str, data in cart.items():
            pid = int(pid_str)
            product = products.get(pid)
            if not product:
                continue
            qty = int(data.get("qty", 1))
            price = Decimal(str(product.price or 0))
            line_total = price * qty
            subtotal += line_total
            items.append({"product": product, "quantity": qty, "line_total": line_total})

        total = subtotal
        return items, subtotal, total

    # ---- address selection stored in session ----
    @staticmethod
    def set_selected_address(session, address_id: int) -> None:
        session[CartService.ADDRESS_KEY] = str(address_id)
        session.modified = True

    @staticmethod
    def get_selected_address_id(session):
        return session.get(CartService.ADDRESS_KEY)

    # # ---- coupon stored in session ----
    # @staticmethod
    # def set_coupon(session, code: str) -> None:
    #     code = (code or "").strip()
    #     if code:
    #         session[CartService.COUPON_KEY] = code
    #     else:
    #         session.pop(CartService.COUPON_KEY, None)
    #     session.modified = True

    # @staticmethod
    # def get_coupon(session):
    #     return (session.get(CartService.COUPON_KEY) or "").strip()