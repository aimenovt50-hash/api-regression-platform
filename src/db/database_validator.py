from __future__ import annotations

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ALLOWED_TABLES = frozenset({"users", "orders", "order_items", "payments", "notifications"})


class DatabaseValidator:
    def __init__(self, database_url: str) -> None:
        self.engine: Engine = create_engine(database_url)

    def count_rows(self, table: str) -> int:
        if table not in ALLOWED_TABLES:
            raise ValueError(f"Table '{table}' is not allowed for validation")
        with self.engine.connect() as connection:
            result = connection.execute(text(f"SELECT COUNT(*) FROM {table}"))
            return int(result.scalar_one())

    def fetch_one(self, query: str, **params) -> dict | None:
        with self.engine.connect() as connection:
            result = connection.execute(text(query), params)
            row = result.mappings().first()
            return dict(row) if row else None

    def user_exists(self, user_id: int) -> bool:
        return self.fetch_one("SELECT id FROM users WHERE id = :user_id", user_id=user_id) is not None

    def user_name(self, user_id: int) -> str | None:
        row = self.fetch_one("SELECT name FROM users WHERE id = :user_id", user_id=user_id)
        return row["name"] if row else None

    def order_status(self, order_id: int) -> str | None:
        row = self.fetch_one("SELECT status FROM orders WHERE id = :order_id", order_id=order_id)
        return row["status"] if row else None

    def payment_for_order(self, order_id: int) -> dict | None:
        return self.fetch_one(
            "SELECT id, order_id, amount, method, status FROM payments WHERE order_id = :order_id",
            order_id=order_id,
        )

    def notification_is_read(self, notification_id: int) -> bool | None:
        row = self.fetch_one(
            "SELECT is_read FROM notifications WHERE id = :notification_id",
            notification_id=notification_id,
        )
        return bool(row["is_read"]) if row else None
