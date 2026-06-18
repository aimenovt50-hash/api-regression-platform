from __future__ import annotations

from typing import Any

import requests

from src.clients.http_client import HttpClient


class AuthClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def register(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/auth/register", json=payload)

    def login(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/auth/login", json=payload)

    def me(self) -> requests.Response:
        return self.client.get("/auth/me")


class UsersClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list_users(self) -> requests.Response:
        return self.client.get("/users")

    def create_user(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/users", json=payload)

    def get_user(self, user_id: int) -> requests.Response:
        return self.client.get(f"/users/{user_id}")

    def update_user(self, user_id: int, payload: dict[str, Any]) -> requests.Response:
        return self.client.patch(f"/users/{user_id}", json=payload)


class OrdersClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list_orders(self) -> requests.Response:
        return self.client.get("/orders")

    def create_order(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/orders", json=payload)

    def get_order(self, order_id: int) -> requests.Response:
        return self.client.get(f"/orders/{order_id}")

    def update_status(self, order_id: int, status: str) -> requests.Response:
        return self.client.patch(f"/orders/{order_id}/status", json={"status": status})


class PaymentsClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def create_payment(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/payments", json=payload)

    def get_payment(self, payment_id: int) -> requests.Response:
        return self.client.get(f"/payments/{payment_id}")

    def get_payment_by_order(self, order_id: int) -> requests.Response:
        return self.client.get(f"/payments/order/{order_id}")


class NotificationsClient:
    def __init__(self, client: HttpClient) -> None:
        self.client = client

    def list_by_user(self, user_id: int) -> requests.Response:
        return self.client.get(f"/notifications/user/{user_id}")

    def create(self, payload: dict[str, Any]) -> requests.Response:
        return self.client.post("/notifications", json=payload)

    def mark_read(self, notification_id: int) -> requests.Response:
        return self.client.patch(f"/notifications/{notification_id}/read")
