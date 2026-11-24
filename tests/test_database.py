import tempfile
import unittest
from pathlib import Path

from database.database import Database


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
