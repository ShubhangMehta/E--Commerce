from decimal import Decimal, ROUND_HALF_UP


class PricingService:
    """
    Single source of truth for pricing.
    """
    ZERO = Decimal("0.00")
    SHIPPING_RATE = Decimal("0.01")   # 1%
    TAX_RATE = Decimal("0.00")        # placeholder for future tax support

    @staticmethod
    def _money(value) -> Decimal:
        return Decimal(value).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    def subtotal_from_items(items) -> Decimal:
        subtotal = sum((item["line_total"] for item in items), start=PricingService.ZERO)
        return PricingService._money(subtotal)

    @staticmethod
    def calculate(*, subtotal: Decimal, coupon=None) -> dict:
        subtotal = PricingService._money(subtotal)

        shipping_amount = PricingService._money(subtotal * PricingService.SHIPPING_RATE)
        tax_amount = PricingService._money(subtotal * PricingService.TAX_RATE)
        discount_amount = PricingService.ZERO
        applied_coupon = None

        if coupon and coupon.is_valid(subtotal):
            discount_amount = PricingService._money(
                subtotal * Decimal(str(coupon.discount_percent)) / Decimal("100")
            )

            if coupon.max_discount:
                discount_amount = min(discount_amount, coupon.max_discount)

            discount_amount = PricingService._money(discount_amount)
            applied_coupon = coupon

        total_amount = subtotal + shipping_amount + tax_amount - discount_amount
        total_amount = max(total_amount, PricingService.ZERO)
        total_amount = PricingService._money(total_amount)

        return {
            "subtotal": subtotal,
            "shipping_amount": shipping_amount,
            "tax_amount": tax_amount,
            "discount_amount": discount_amount,
            "total_amount": total_amount,
            "coupon": applied_coupon,
        }

    @staticmethod
    def calculate_from_items(*, items, coupon=None) -> dict:
        subtotal = PricingService.subtotal_from_items(items)
        return PricingService.calculate(subtotal=subtotal, coupon=coupon)