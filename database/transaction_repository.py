from __future__ import annotations

import sqlite3
from uuid import UUID

from models.transaction import Transaction


class TransactionRepository:

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._transactions: dict[UUID, Transaction] = {}

    # Method to save new transaction in dictionary (key - transaction.id : value - transaction)
    def save(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Provided transaction must be instance of Transaction class.")

        self._transactions[transaction.id] = transaction

    # Method returns list of transactions (Transaction class) without keys
    def get_all(self) -> list[Transaction]:
        return list(self._transactions.values())

    # Method to search the transaction using id, returns Transaction or None if not found
    def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        return self._transactions.get(transaction_id)