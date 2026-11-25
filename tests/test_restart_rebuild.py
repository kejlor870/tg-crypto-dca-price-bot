import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from database.database import Database
from database.transaction_repository import TransactionRepository
from services.transaction_service import TransactionService


class TestRestartRebuild(unittest.TestCase):

    def test_rebuild_portfolios_after_restart(self):
        with tempfile.TemporaryDirectory() as tmp_dir:

            db_path = str(Path(tmp_dir) / "test.db")

            # 1. First init - save BTC and close db
            db_first = Database(str(db_path))
            db_first.initialize()

            repo_first = TransactionRepository(db_first.connection)
            service_first = TransactionService(repo_first)

            service_first.add_buy("BTC", Decimal("0.5"), Decimal("60000"))

            db_first.close()

            # 2. Restart simulation
            db_restarted = Database(str(db_path))
            db_restarted.initialize()

            repo_restarted = TransactionRepository(db_restarted.connection)
            service_restarted = TransactionService(repo_restarted)

            service_restarted.rebuild_portfolios()

            portfolio = service_restarted.get_portfolio("BTC")

            self.assertIsNotNone(portfolio)
            self.assertEqual(Decimal("0.5"), portfolio.quantity)
            self.assertEqual(Decimal("60000"), portfolio.average_buy_price)

            db_restarted.close()
