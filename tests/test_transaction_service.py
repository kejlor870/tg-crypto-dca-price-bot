import unittest
from decimal import Decimal

from database.transaction_repository import TransactionRepository
from models.transaction import Transaction, TransactionType
from services.transaction_service import TransactionService


class TestTransactionService(unittest.TestCase):

    def setUp(self):
        self.tx_repository = TransactionRepository()
        self.service = TransactionService(self.tx_repository)

    def test_add_buy_returns_buy_transaction(self) -> None:

        tx = self.service.add_buy("BTC", Decimal("0.5"), Decimal("61000"))

        self.assertIsInstance(tx, Transaction)
        self.assertEqual(TransactionType.BUY, tx.transaction_type)
        self.assertEqual("BTC", tx.symbol)
        self.assertEqual(Decimal("0.5"), tx.quantity)
        self.assertEqual(Decimal("61000"), tx.price)

    def test_add_buy_creates_portfolio_for_new_symbol(self) -> None:

        self.service.add_buy("btc", Decimal("0.5"), Decimal("60000"))

        self.assertIn("BTC", self.service._portfolios)
        self.assertEqual(1, len(self.service._portfolios))

    def test_second_buy_updates_existing_portfolio_instead_of_creating_new(self) -> None:

        self.service.add_buy("BTC", Decimal("0.5"), Decimal("60000"))
        portfolio_after_first = self.service._portfolios["BTC"]

        self.service.add_buy("btc", Decimal("1.5"), Decimal("62000"))
        portfolio_after_second = self.service._portfolios["BTC"]

        self.assertEqual(1, len(self.service._portfolios))
        self.assertIs(portfolio_after_first, portfolio_after_second)
        self.assertEqual(Decimal("2.0"), portfolio_after_second.quantity)

    def test_add_buy_saves_transaction_in_repository(self) -> None:

        tx = self.service.add_buy("ETH", Decimal("2.0"), Decimal("3000"))

        saved = self.tx_repository.get_by_id(tx.id)
        self.assertEqual(tx, saved)
        self.assertEqual(1, len(self.tx_repository.get_all()))

    def test_invalid_quantity_or_price_raises_and_does_not_save(self) -> None:
        invalid_cases = [
            (Decimal("0"), Decimal("60000")),
            (Decimal("-1"), Decimal("60000")),
            (Decimal("0.5"), Decimal("0")),
            (Decimal("0.5"), Decimal("-100")),
        ]

        for bad_quantity, bad_price in invalid_cases:
            with self.subTest(quantity=bad_quantity, price=bad_price):
                repo = TransactionRepository()
                service = TransactionService(repo)

                with self.assertRaises((ValueError, TypeError)):
                    service.add_buy("BTC", bad_quantity, bad_price)

                self.assertEqual(0, len(repo.get_all()))
