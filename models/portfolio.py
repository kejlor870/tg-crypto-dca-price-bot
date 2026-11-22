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

        if not isinstance(quantity, Decimal) or quantity < Decimal("0"):
            raise ValueError("Quantity must be greater than zero.")

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

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def total_cost(self) -> Decimal:
        return self._total_cost

    def buy(self, quantity: Decimal, price: Decimal) -> None:
        if not isinstance(quantity, Decimal):
            raise TypeError("Quantity must be in DECIMAL type.")
        if not isinstance(price, Decimal):
            raise TypeError("Price must be in DECIMAL type.")

        if quantity <= Decimal("0"):
            raise ValueError("Quantity must be greater or equal 0.")
        if price <= Decimal("0"):
            raise ValueError("Price must be greater or equal 0.")

        cost = quantity * price

        self._quantity += quantity
        self._total_cost += cost

    def sell(self, quantity: Decimal, price: Decimal) -> None:
        if not isinstance(quantity, Decimal):
            raise TypeError("Quantity must be in DECIMAL type.")
        if not isinstance(price, Decimal):
            raise TypeError("Price must be in DECIMAL type.")

        if quantity <= Decimal("0"):
            raise ValueError("Quantity must be greater than 0.")
        if price <= Decimal("0"):
            raise ValueError("Price must be greater than 0.")

        if self._quantity < quantity:
            raise ValueError("Can not sell more than is in total quantity.")

        avg_buy_price = self.average_buy_price

        self._quantity -= quantity
        if self._quantity == Decimal("0"):
            self._total_cost = Decimal("0")
        else:
            self._total_cost -= quantity * avg_buy_price
