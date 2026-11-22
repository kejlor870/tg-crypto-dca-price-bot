from decimal import Decimal


class Portfolio:
    def __init__(
            self,
            symbol: str,
            quantity: Decimal,
            total_cost: Decimal
    ) -> None:
        if not symbol or not symbol.strip():
            raise ValueError("Symbol can not be empty.")

        if not isinstance(quantity, Decimal) or quantity <= Decimal("0"):
            raise ValueError("Quantity must be greater or equal zero.")

        if not isinstance(total_cost, Decimal) or total_cost < Decimal("0"):
            raise ValueError("Total cost must be greater or equal zero.")

        self._symbol = symbol.strip().upper()
        self._quantity = quantity
        self._total_cost = total_cost

    @property
    def average_buy_price(self) -> Decimal:
        if self._quantity == Decimal("0"):
            return Decimal("0")

        return self._total_cost / self._quantity
