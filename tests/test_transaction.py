import unittest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from models.transaction import Transaction, TransactionType


class TestTransaction(unittest.TestCase):

    def test_valid_transaction_creation(self):
        tx_type = TransactionType.BUY
        tx_symbol = "BTC"
        tx_quantity = Decimal("0.05")
        tx_price = Decimal("67000.0")

        tx = Transaction(
            transaction_type=tx_type,
            symbol=tx_symbol,
            quantity=tx_quantity,
            price=tx_price
        )

        self.assertIsInstance(tx.id, UUID)
        self.assertIsInstance(tx.created_at, datetime)
        self.assertEqual(tx.created_at.tzinfo, timezone.utc)
        self.assertEqual(tx.transaction_type, tx_type)
        self.assertEqual(tx.symbol, tx_symbol)
        self.assertEqual(tx.quantity, tx_quantity)
        self.assertEqual(tx.price, tx_price)

    def test_normalize_transaction_symbol(self):
        tx_type = TransactionType.BUY
        tx_symbol = "btc"
        tx_quantity = Decimal("0.05")
        tx_price = Decimal("67000.0")

        tx = Transaction(
            transaction_type=tx_type,
            symbol=tx_symbol,
            quantity=tx_quantity,
            price=tx_price
        )

        self.assertEqual(tx.symbol, "BTC")

    def test_transaction_value(self):
        tx_type = TransactionType.BUY
        tx_symbol = "BTC"
        tx_quantity = Decimal("0.015")
        tx_price = Decimal("92000.0")

        tx = Transaction(
            transaction_type=tx_type,
            symbol=tx_symbol,
            quantity=tx_quantity,
            price=tx_price
        )

        self.assertEqual(tx.value, Decimal("1380.0"))

    def test_incorrect_transaction_type(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type="BUY",     # Correct: TransactionType.BUY
                symbol="BTC",
                quantity=Decimal("0.015"),
                price=Decimal("92000.0")
            )

    def test_incorrect_transaction_quantity(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type="BUY",
                symbol="BTC",
                quantity=Decimal("0.0"),      # Correct: > 0
                price=Decimal("92000.0")
            )

    def test_incorrect_transaction_price(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type="BUY",
                symbol="BTC",
                quantity=Decimal("0.015"),
                price=Decimal("0.0")     # Correct: > 0
            )

    def test_incorrect_transaction_symbol(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type="BUY",
                symbol="  ",       # Correct: any text
                quantity=Decimal("0.015"),
                price=Decimal("32000.0")
            )

    def test_quantity_as_float_raises_error(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=1.5,  # type: ignore
                price=Decimal("50000")
            )

    def test_price_as_float_raises_error(self):
        with self.assertRaises(ValueError):
            Transaction(
                transaction_type=TransactionType.BUY,
                symbol="BTC",
                quantity=Decimal("1.5"),
                price=50000.50  # type: ignore
            )
