from __future__ import annotations

from decimal import Decimal
from uuid import UUID

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

        current_portfolio = self._portfolios.get(normalized_symbol)

        # If portfolio for given symbol doesn't exist create new empty Portfolio and
        #   add it to dictionary
        if current_portfolio is None:
            current_portfolio = Portfolio(normalized_symbol, Decimal("0"), Decimal("0"))

        # Add buy Transaction to transaction repository
        self._repository.save(new_transaction)
        # Change portfolio for provided coin
        current_portfolio.buy(quantity, price)

        self._portfolios[normalized_symbol] = current_portfolio

        return new_transaction

    def add_sell(self, symbol: str, quantity: Decimal, price: Decimal) -> Transaction:
        if not symbol or not symbol.strip():
            raise ValueError("Symbol can not be empty.")

        normalized_symbol = symbol.strip().upper()

        current_portfolio = self._portfolios.get(normalized_symbol)

        if normalized_symbol not in self._portfolios:
            raise ValueError("Not found portfolio for provided symbol.")

        new_transaction = Transaction(TransactionType.SELL, normalized_symbol, quantity, price)

        if quantity > current_portfolio.quantity:
            raise ValueError("Cannot sell more than the current portfolio quantity.")

        # Add new sell transaction to transaction repository
        self._repository.save(new_transaction)
        # Update portfolio for coin - quantity and total_cost
        current_portfolio.sell(quantity, price)

        return new_transaction

    def get_portfolio(self, symbol: str) -> Portfolio | None:
        if not symbol or not symbol.strip():
            raise ValueError("Symbol can not be empty.")

        normalized_symbol = symbol.strip().upper()

        return self._portfolios.get(normalized_symbol)

    def get_all_portfolios(self) -> list[Portfolio]:
        return list(self._portfolios.values())

    def get_all_transactions(self) -> list[Transaction]:
        return self._repository.get_all()

    def delete_transaction(self, transaction_id: UUID) -> bool:
        # Check whether the transaction exists.
        transaction = self._repository.get_by_id(transaction_id)

        if transaction is None:
            return False

        # Load all transactions except the one we want to delete.
        remaining_transactions = [
            tx for tx in self._repository.get_all()
            if tx.id != transaction_id
        ]

        # Validate the remaining history using temporary portfolios.
        test_portfolios: dict[str, Portfolio] = {}

        for tx in reversed(remaining_transactions):
            symbol = tx.symbol

            if tx.transaction_type == TransactionType.BUY:
                if symbol not in test_portfolios:
                    test_portfolios[symbol] = Portfolio(
                        symbol,
                        Decimal("0"),
                        Decimal("0")
                    )

                test_portfolios[symbol].buy(tx.quantity, tx.price)

            elif tx.transaction_type == TransactionType.SELL:
                if symbol not in test_portfolios:
                    raise ValueError(
                        f"Cannot delete this transaction: "
                        f"remaining history contains a SELL without a previous BUY for {symbol}."
                    )

                test_portfolios[symbol].sell(tx.quantity, tx.price)

            else:
                raise ValueError(f"Unsupported transaction type: {tx.transaction_type}")

        # The remaining history is valid, so delete the transaction.
        deleted = self._repository.delete_by_id(transaction_id)

        if not deleted:
            return False

        # Recalculate the real portfolios from the remaining history.
        self.rebuild_portfolios()

        return True

    def rebuild_portfolios(self) -> None:
        self._portfolios.clear()

        transactions = self._repository.get_all()

        for transaction in reversed(transactions):
            symbol = transaction.symbol

            # BUY
            if transaction.transaction_type == TransactionType.BUY:
                # If coin symbol not have portfolio - create it
                if symbol not in self._portfolios:
                    self._portfolios[symbol] = Portfolio(
                        symbol,
                        Decimal("0"),
                        Decimal("0")
                    )

                self._portfolios[symbol].buy(transaction.quantity, transaction.price)

            # SELL
            elif transaction.transaction_type == TransactionType.SELL:
                if symbol not in self._portfolios:
                    raise ValueError(f"Can not rebuild portfolio for {symbol}: \nSELL transaction without previous BUY.")

                self._portfolios[symbol].sell(transaction.quantity, transaction.price)

            else:
                raise ValueError(f"Unsupported transaction type: {transaction.transaction_type}")

            # service.rebuild_portfolios()
