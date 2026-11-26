
import unittest
from decimal import Decimal

from database.database import Database
from database.transaction_repository import TransactionRepository
from models.portfolio import Portfolio
from models.transaction import Transaction, TransactionType
from services.transaction_service import TransactionService


class TestTransactionService(unittest.TestCase):

    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.db.initialize()

        self.tx_repository = TransactionRepository(self.db.connection)
        self.service = TransactionService(self.tx_repository)

    def tearDown(self) -> None:
        self.db.close()

    def test_add_buy_returns_buy_transaction(self) -> None:
        tx = self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("61000")
        )

        self.assertIsInstance(tx, Transaction)
        self.assertEqual(TransactionType.BUY, tx.transaction_type)
        self.assertEqual("BTC", tx.symbol)
        self.assertEqual(Decimal("0.5"), tx.quantity)
        self.assertEqual(Decimal("61000"), tx.price)

    def test_add_buy_creates_portfolio_for_new_symbol(self) -> None:
        self.service.add_buy(
            "btc", Decimal("0.5"), Decimal("60000")
        )

        self.assertIn("BTC", self.service._portfolios)
        self.assertEqual(1, len(self.service._portfolios))

    def test_second_buy_updates_existing_portfolio_instead_of_creating_new(self) -> None:
        self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("60000")
        )
        portfolio_after_first = self.service._portfolios["BTC"]

        self.service.add_buy(
            "btc", Decimal("1.5"), Decimal("62000")
        )
        portfolio_after_second = self.service._portfolios["BTC"]

        self.assertEqual(1, len(self.service._portfolios))
        self.assertIs(portfolio_after_first, portfolio_after_second)
        self.assertEqual(Decimal("2.0"), portfolio_after_second.quantity)

    def test_add_buy_saves_transaction_in_repository(self) -> None:
        tx = self.service.add_buy(
            "ETH", Decimal("2.0"), Decimal("3000")
        )

        saved = self.tx_repository.get_by_id(tx.id)

        self.assertIsNotNone(saved)
        self.assertEqual(tx.id, saved.id)
        self.assertEqual(tx.symbol, saved.symbol)
        self.assertEqual(tx.quantity, saved.quantity)
        self.assertEqual(tx.price, saved.price)
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
                with self.assertRaises((ValueError, TypeError)):
                    self.service.add_buy(
                        "BTC", bad_quantity, bad_price
                    )

                self.assertEqual(0, len(self.tx_repository.get_all()))

    # --------- SELL ---------

    def test_add_sell_partial_quantity_updates_portfolio_and_repository(self) -> None:
        self.service.add_buy(
            "BTC", Decimal("1.5"), Decimal("60000")
        )

        sell_tx = self.service.add_sell(
            "btc", Decimal("0.5"), Decimal("65000")
        )

        self.assertIsInstance(sell_tx, Transaction)
        self.assertEqual(TransactionType.SELL, sell_tx.transaction_type)
        self.assertEqual("BTC", sell_tx.symbol)
        self.assertEqual(Decimal("0.5"), sell_tx.quantity)
        self.assertEqual(Decimal("65000"), sell_tx.price)

        portfolio = self.service._portfolios["BTC"]
        self.assertEqual(Decimal("1.0"), portfolio.quantity)

        self.assertEqual(2, len(self.tx_repository.get_all()))
        saved = self.tx_repository.get_by_id(sell_tx.id)

        self.assertIsNotNone(saved)
        self.assertEqual(sell_tx.id, saved.id)
        self.assertEqual(sell_tx.transaction_type, saved.transaction_type)
        self.assertEqual(sell_tx.symbol, saved.symbol)
        self.assertEqual(sell_tx.quantity, saved.quantity)
        self.assertEqual(sell_tx.price, saved.price)

    def test_add_sell_more_than_owned_raises_value_error_and_does_not_save(self) -> None:
        self.service.add_buy(
            "ETH", Decimal("2.0"), Decimal("3000")
        )

        with self.assertRaises(ValueError):
            self.service.add_sell(
                "ETH", Decimal("3.0"), Decimal("3200")
            )

        portfolio = self.service._portfolios["ETH"]
        self.assertEqual(Decimal("2.0"), portfolio.quantity)
        self.assertEqual(1, len(self.tx_repository.get_all()))

    def test_add_sell_for_nonexistent_portfolio_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            self.service.add_sell(
                "SOL", Decimal("1.0"), Decimal("150")
            )

        self.assertNotIn("SOL", self.service._portfolios)
        self.assertEqual(0, len(self.tx_repository.get_all()))

    # ---------- Portfolio methods ----------

    def test_get_portfolio_returns_correct_portfolio(self) -> None:
        self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("61000")
        )
        self.service.add_buy(
            "BTC", Decimal("0.2"), Decimal("70000")
        )

        portfolio_btc = self.service.get_portfolio("BTC")

        self.assertIsInstance(portfolio_btc, Portfolio)
        self.assertIs(self.service.get_portfolio("BTC"), portfolio_btc)

    def test_get_portfolio_lowercase_symbol_works(self) -> None:
        self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("61000")
        )

        portfolio_btc = self.service.get_portfolio("btc")

        self.assertIsInstance(portfolio_btc, Portfolio)
        self.assertIs(self.service.get_portfolio("BTC"), portfolio_btc)

    def test_get_portfolio_nonexistent_symbol_returns_none(self) -> None:
        portfolio = self.service.get_portfolio("nonExists")

        self.assertIsNone(portfolio)

    def test_get_portfolio_empty_symbol_raises_value_error(self) -> None:
        for empty_symbol in ["", "  "]:
            with self.subTest(symbol=empty_symbol):
                with self.assertRaises(ValueError):
                    self.service.get_portfolio(empty_symbol)

    def test_get_all_portfolios_returns_all_created_portfolios(self) -> None:
        self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("60000")
        )
        self.service.add_buy(
            "ETH", Decimal("2.0"), Decimal("3000")
        )

        portfolios = self.service.get_all_portfolios()

        self.assertEqual(2, len(portfolios))
        self.assertIn(self.service._portfolios["BTC"], portfolios)
        self.assertIn(self.service._portfolios["ETH"], portfolios)

    def test_get_all_transactions_returns_saved_transactions(self) -> None:
        tx1 = self.service.add_buy(
            "BTC", Decimal("0.5"), Decimal("60000")
        )
        tx2 = self.service.add_buy(
            "ETH", Decimal("2.0"), Decimal("3000")
        )

        transactions = self.service.get_all_transactions()

        self.assertEqual(2, len(transactions))

        transaction_ids = [tx.id for tx in transactions]

        self.assertIn(tx1.id, transaction_ids)
        self.assertIn(tx2.id, transaction_ids)


if __name__ == "__main__":
    unittest.main()
