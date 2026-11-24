import tempfile
import unittest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from database.database import Database
from database.transaction_repository import TransactionRepository
from models.transaction import Transaction, TransactionType


class TestDatabase(unittest.TestCase):

    def test_initialize_creates_transactions_table(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "test.db")
            db = Database(db_path)

            try:
                db.initialize()
                row = db._connection.execute(
                    """
                    SELECT name
                    FROM sqlite_master
                    WHERE type = 'table' AND name = 'transactions';
                    """
                ).fetchone()

            finally:
                db.close()

            self.assertIsNotNone(row)
            self.assertEqual("transactions", row[0])


    # ------------ Transaction repository db ------------
    def test_db_connection_transaction_repo(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "test.db")
            db = Database(db_path)

            try:
                db.initialize()
                tr_repository = TransactionRepository(db.connection)
                tx = Transaction(TransactionType.BUY, "BTC", Decimal("0.05"), Decimal("59000"))

                # Saving transaction to database
                tr_repository.save(tx)

                row = db.connection.execute(
                    """
                    SELECT id, transaction_type, symbol, quantity, price, created_at
                    FROM transactions
                    WHERE id = ?
                    """,
                    (
                        str(tx.id),
                    )
                ).fetchone()

            finally:
                db.close()

            self.assertIsNotNone(row)
            self.assertEqual(str(tx.id), row[0])
            self.assertEqual("BUY", row[1])
            self.assertEqual("BTC", row[2])
            self.assertEqual("0.05", row[3])
            self.assertEqual("59000", row[4])
            self.assertEqual(tx.created_at.isoformat(), row[5])

    def test_db_transaction_repo_get_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "test.db")
            db = Database(db_path)

            try:
                db.initialize()
                tr_repository = TransactionRepository(db.connection)
                tx = Transaction(TransactionType.BUY, "ETH", Decimal("1"), Decimal("1700"))
                tr_repository.save(tx)

                result_tx = tr_repository.get_by_id(tx.id)

            finally:
                db.close()

            self.assertIsNotNone(result_tx)
            self.assertEqual(tx.id, result_tx.id)
            self.assertEqual(tx.transaction_type, result_tx.transaction_type)
            self.assertEqual(tx.symbol, result_tx.symbol)
            self.assertEqual(tx.quantity, result_tx.quantity)
            self.assertEqual(tx.price, result_tx.price)
            self.assertEqual(tx.created_at, result_tx.created_at)

    def test_db_transaction_repo_get_by_id_invalid(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "test.db")
            db = Database(db_path)

            try:
                db.initialize()
                tr_repository = TransactionRepository(db.connection)

                result_tx = tr_repository.get_by_id(uuid4())

            finally:
                db.close()

        self.assertIsNone(result_tx)

    def test_db_transaction_repo_get_all(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = str(Path(tmp_dir) / "test.db")
            db = Database(db_path)

            try:
                db.initialize()
                tr_repository = TransactionRepository(db.connection)

                base_time = datetime(2026, 1, 10, 12, 0, tzinfo=timezone.utc)
                oldest_tx = Transaction.from_db(
                    uuid4(),
                    base_time,
                    TransactionType.BUY,
                    "BTC",
                    Decimal("0.25"),
                    Decimal("58000"),
                )
                middle_tx = Transaction.from_db(
                    uuid4(),
                    base_time + timedelta(hours=2),
                    TransactionType.BUY,
                    "ETH",
                    Decimal("1.5"),
                    Decimal("3100"),
                )
                newest_tx = Transaction.from_db(
                    uuid4(),
                    base_time + timedelta(days=1),
                    TransactionType.SELL,
                    "BTC",
                    Decimal("0.1"),
                    Decimal("62000"),
                )

                for tx in (middle_tx, oldest_tx, newest_tx):
                    tr_repository.save(tx)

                results = tr_repository.get_all()

            finally:
                db.close()

            self.assertEqual(3, len(results))
            self.assertEqual(
                [newest_tx.id, middle_tx.id, oldest_tx.id],
                [tx.id for tx in results],
            )
            expected_order = [newest_tx, middle_tx, oldest_tx]
            for actual, expected in zip(results, expected_order):
                self.assertEqual(expected.id, actual.id)
                self.assertEqual(expected.created_at, actual.created_at)
                self.assertEqual(expected.transaction_type, actual.transaction_type)
                self.assertEqual(expected.symbol, actual.symbol)
                self.assertEqual(expected.quantity, actual.quantity)
                self.assertEqual(expected.price, actual.price)
