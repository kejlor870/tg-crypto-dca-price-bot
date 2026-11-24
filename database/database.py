import sqlite3


class Database:

    def __init__(self, db_path: str) -> None:
        self._connection: sqlite3.Connection = sqlite3.connect(db_path)

    def close(self) -> None:
        self._connection.close()

    def initialize(self) -> None:
        self._connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id TEXT PRIMARY KEY,
                transaction_type TEXT NOT NULL,
                symbol TEXT NOT NULL,
                quantity TEXT NOT NULL,
                price TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self._connection.commit()

    def connection(self):
        return self._connection
