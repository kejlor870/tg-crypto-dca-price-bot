
import unittest
from decimal import Decimal
from uuid import uuid4

from database.database import Database
from database.transaction_repository import TransactionRepository
from models.transaction import Transaction, TransactionType


class TestTransactionRepository(unittest.TestCase):

    def setUp(self) -> None:
        self.db = Database(":memory:")
        self.db.initialize()
        self.trepo = TransactionRepository(self.db.connection)

        self.tx1 = Transaction(
            TransactionType.BUY,
            "BTC",
            Decimal("0.5"),
            Decimal("60000"),
        )
        self.tx2 = Transaction(
            TransactionType.SELL,
            "ETH",
            Decimal("2.0"),
            Decimal("3000"),
        )

    def tearDown(self) -> None:
        self.db.close()

    def test_save_transaction(self) -> None:
        self.trepo.save(self.tx1)

        self.assertEqual(1, len(self.trepo.get_all()))

        saved = self.trepo.get_by_id(self.tx1.id)

        self.assertIsNotNone(saved)
        self.assertEqual(self.tx1.id, saved.id)
        self.assertEqual(self.tx1.symbol, saved.symbol)
        self.assertEqual(self.tx1.quantity, saved.quantity)
        self.assertEqual(self.tx1.price, saved.price)

    def test_get_all_returns_saved_transactions(self) -> None:
        self.trepo.save(self.tx1)
        self.trepo.save(self.tx2)

        all_txs = self.trepo.get_all()

        self.assertEqual(2, len(all_txs))

        saved_ids = [tx.id for tx in all_txs]

        self.assertIn(self.tx1.id, saved_ids)
        self.assertIn(self.tx2.id, saved_ids)

    def test_get_by_id_returns_matching_transaction(self) -> None:
        self.trepo.save(self.tx1)
        self.trepo.save(self.tx2)

        found = self.trepo.get_by_id(self.tx2.id)

        self.assertIsNotNone(found)
        self.assertEqual(self.tx2.id, found.id)
        self.assertEqual(self.tx2.symbol, found.symbol)
        self.assertEqual(self.tx2.quantity, found.quantity)
        self.assertEqual(self.tx2.price, found.price)

    def test_get_by_id_returns_none_for_missing_id(self) -> None:
        result = self.trepo.get_by_id(uuid4())

        self.assertIsNone(result)

    def test_save_raises_type_error_for_invalid_object(self) -> None:
        with self.assertRaises(TypeError):
            self.trepo.save("niepoprawny obiekt")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
