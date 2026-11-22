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
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("0"),
            total_cost=Decimal("0")
        )

        self.assertEqual(portfolio.average_buy_price, Decimal("0"))

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

    def test_buy_increase_quantity_and_total_cost(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("0.2"),
            total_cost=Decimal("10000")
        )

        portfolio.buy(quantity=Decimal("0.3"), price=Decimal("60000"))

        self.assertEqual(portfolio.quantity, Decimal("0.5"))
        self.assertEqual(portfolio.total_cost, Decimal("28000"))

    def test_buy_updates_average_buy_price(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        # Buy 1 BTC for 70 000 -> 2 BTC for 120 000 -> avg 60 000
        portfolio.buy(quantity=Decimal("1"), price=Decimal("70000"))

        self.assertEqual(portfolio.average_buy_price, Decimal("60000"))

    def test_buy_zero_quantity_raises_value_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.assertRaises(ValueError):
            portfolio.buy(quantity=Decimal("0"), price=Decimal("50000"))

    def test_buy_zero_price_raises_value_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.assertRaises(ValueError):
            portfolio.buy(quantity=Decimal("1"), price=Decimal("0"))

    def test_buy_float_arguments_raise_type_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.subTest("quantity as float"):
            with self.assertRaises(TypeError):
                portfolio.buy(quantity=0.5, price=Decimal("50000"))  # type: ignore

        with self.subTest("price as float"):
            with self.assertRaises(TypeError):
                portfolio.buy(quantity=Decimal("0.5"), price=50000.0)  # type: ignore

    def test_sell_partial_position_reduces_quantity_and_cost(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("2"),
            total_cost=Decimal("100000")
        )

        portfolio.sell(quantity=Decimal("0.5"), price=Decimal("70000"))

        self.assertEqual(portfolio.quantity, Decimal("1.5"))
        self.assertEqual(portfolio.total_cost, Decimal("75000"))
        self.assertEqual(portfolio.average_buy_price, Decimal("50000"))

    def test_sell_entire_position_resets_quantity_and_cost_to_zero(self):
        portfolio = Portfolio(
            symbol="SOL",
            quantity=Decimal("3"),
            total_cost=Decimal("100")
        )

        portfolio.sell(quantity=Decimal("3"), price=Decimal("50"))

        self.assertEqual(portfolio.quantity, Decimal("0"))
        self.assertEqual(portfolio.total_cost, Decimal("0"))
        self.assertEqual(portfolio.average_buy_price, Decimal("0"))

    def test_sell_more_than_owned_raises_value_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.assertRaises(ValueError):
            portfolio.sell(quantity=Decimal("1.1"), price=Decimal("60000"))

    def test_sell_zero_quantity_raises_value_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.assertRaises(ValueError):
            portfolio.sell(quantity=Decimal("0"), price=Decimal("60000"))

    def test_sell_zero_price_raises_value_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.assertRaises(ValueError):
            portfolio.sell(quantity=Decimal("0.5"), price=Decimal("0"))

    def test_sell_float_arguments_raise_type_error(self):
        portfolio = Portfolio(
            symbol="BTC",
            quantity=Decimal("1"),
            total_cost=Decimal("50000")
        )

        with self.subTest("quantity as float"):
            with self.assertRaises(TypeError):
                portfolio.sell(quantity=0.5, price=Decimal("60000"))  # type: ignore

        with self.subTest("price as float"):
            with self.assertRaises(TypeError):
                portfolio.sell(quantity=Decimal("0.5"), price=60000.0)  # type: ignore
