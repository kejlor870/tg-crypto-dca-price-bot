from __future__ import annotations

import sqlite3
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from models.transaction import Transaction, TransactionType


class TransactionRepository:

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    # Method to save new transaction in dictionary (key - transaction.id : value - transaction)
    def save(self, transaction: Transaction) -> None:
        if not isinstance(transaction, Transaction):
            raise TypeError("Provided transaction must be instance of Transaction class.")

        try:
            self._connection.execute(
                """
                INSERT INTO transactions (id, transaction_type, symbol, quantity, price, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    str(transaction.id),
                    transaction.transaction_type.value,
                    transaction.symbol,
                    str(transaction.quantity),
                    str(transaction.price),
                    transaction.created_at.isoformat()
                )
            )
            self._connection.commit()

        except sqlite3.Error:
            self._connection.rollback()
            raise

    # Method returns list of transactions (Transaction class) without keys
    def get_all(self) -> list[Transaction]:
        rows = self._connection.execute(
            """
            SELECT id, transaction_type, symbol, quantity, price, created_at
            FROM transactions ORDER BY created_at DESC
            """
        ).fetchall()

        return [
            Transaction.from_db(
                UUID(row[0]),
                datetime.fromisoformat(row[5]),
                TransactionType(row[1]),
                row[2],
                Decimal(row[3]),
                Decimal(row[4])
            )
            for row in rows
        ]

    # Method to search the transaction using id, returns Transaction or None if not found
    def get_by_id(self, transaction_id: UUID) -> Transaction | None:
        row = self._connection.execute(
            """
            SELECT id, transaction_type, symbol, quantity, price, created_at
            FROM transactions
            WHERE id = ?
            """,
            (
                str(transaction_id),
            )
        ).fetchone()

        if row is None:
            return None

        tx_id = UUID(row[0])
        transaction_type = TransactionType(row[1])
        symbol = row[2]
        quantity = Decimal(row[3])
        price = Decimal(row[4])
        created_at = datetime.fromisoformat(row[5])

        searched_tx = Transaction.from_db(tx_id, created_at, transaction_type, symbol, quantity, price)

        return searched_tx
