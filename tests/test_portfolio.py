import unittest
from decimal import Decimal

from models.portfolio import Portfolio


class TestPortfolio(unittest.TestCase):

    def test_valid_portfolio_creation(self):
        portfolio = Portfolio(
            symbol="  btc ",
            quantity=Decimal("0.5"),
            total_cost=Decimal("25000")
        )

        self.assertEqual(portfolio.symbol, "BTC")
        self.assertEqual(portfolio.quantity, Decimal("0.5"))
        self.assertEqual(portfolio.total_cost, Decimal("25000"))

    def test_average_buy_price_calculation(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("0.2"),
            total_cost=Decimal("14000")
        )

        self.assertEqual(portfolio.average_buy_price, Decimal("70000"))

    def test_average_buy_price_when_quantity_is_zero(self):
        with self.assertRaises(ValueError):
            Portfolio(
                symbol="BTC",
                quantity=Decimal("0"),
                total_cost=Decimal("0")
            )

    def test_empty_symbol_raises_error(self):
        for invalid_symbol in ["", "   "]:
            with self.subTest(symbol=invalid_symbol):
                with self.assertRaises(ValueError):
                    Portfolio(
                        symbol=invalid_symbol,
                        quantity=Decimal("1"),
                        total_cost=Decimal("100")
                    )

    def test_negative_quantity_raises_error(self):
        with self.assertRaises(ValueError):
            Portfolio(
                symbol="BTC",
                quantity=Decimal("-0.1"),
                total_cost=Decimal("100")
            )

    def test_negative_total_cost_raises_error(self):
        with self.assertRaises(ValueError):
            Portfolio(
                symbol="BTC",
                quantity=Decimal("1"),
                total_cost=Decimal("-500")
            )