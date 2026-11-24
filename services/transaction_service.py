from decimal import Decimal

from database.transaction_repository import TransactionRepository
from models.portfolio import Portfolio
from models.transaction import Transaction, TransactionType


class TransactionService:

    def __init__(self, tr_repository: TransactionRepository) -> None:
        self._repository = tr_repository
        self._portfolios: dict[str, Portfolio] = {}

    def add_buy(self, symbol: str, quantity: Decimal, price: Decimal) -> Transaction:
        if not symbol or not symbol.strip():
            raise ValueError("Symbol can not be empty.")

        normalized_symbol = symbol.strip().upper()

        new_transaction = Transaction(TransactionType.BUY, normalized_symbol, quantity, price)

        # If portfolio for given symbol doesn't exist create new empty Portfolio and
        #   add it to dictionary
        if normalized_symbol not in self._portfolios:
            self._portfolios[normalized_symbol] = Portfolio(normalized_symbol, Decimal("0"), Decimal("0"))

        current_portfolio = self._portfolios[normalized_symbol]

        # Change portfolio for provided coin
        current_portfolio.buy(quantity, price)
        # Add buy Transaction to transaction repository
        self._repository.save(new_transaction)

        return new_transaction
