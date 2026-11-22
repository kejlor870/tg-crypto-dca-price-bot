from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from enum import StrEnum


class TransactionType(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class Transaction:
    def __init__(
            self,
            transaction_type: TransactionType,
            symbol: str,
            quantity: Decimal,
            price: Decimal
    ) -> None:
        if not isinstance(transaction_type, TransactionType):
            raise ValueError("Incorrect transaction type. Use TransactionType.BUY or SELL.")

        if not symbol or symbol.strip():
            raise ValueError("Symbol can not be empty.")

        if not isinstance(quantity, Decimal) or quantity <= Decimal("0"):
            raise ValueError("Quantity must be greater than zero.")

        if not isinstance(price, Decimal) or price <= Decimal("0"):
            raise ValueError("Price must be greater than zero.")

        self._id = uuid4()
        self._created_at = datetime.now(timezone.utc)
        self._transaction_type = transaction_type
        self._symbol = symbol.strip().upper()
        self._quantity = quantity
        self._price = price

    @property
    def id(self) -> UUID:
        return self._id

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def transaction_type(self) -> TransactionType:
        return self._transaction_type

    @property
    def symbol(self) -> str:
        return self._symbol

    @property
    def quantity(self) -> Decimal:
        return self._quantity

    @property
    def price(self) -> Decimal:
        return self._price

    @property
    def value(self) -> Decimal:
        return self._quantity * self._price
