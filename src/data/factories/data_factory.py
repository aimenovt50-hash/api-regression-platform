from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from faker import Faker


@dataclass(frozen=True)
class AuthPayload:
    email: str
    password: str
    name: str


@dataclass(frozen=True)
class UserPayload:
    email: str
    name: str
    role: str = "user"


@dataclass(frozen=True)
class OrderItemPayload:
    product_id: str
    quantity: int
    price: float


@dataclass(frozen=True)
class OrderPayload:
    user_id: int
    items: tuple[OrderItemPayload, ...]


@dataclass(frozen=True)
class PaymentPayload:
    order_id: int
    amount: float
    method: str


@dataclass(frozen=True)
class NotificationPayload:
    user_id: int
    channel: str
    message: str


class DataFactory:
    _faker = Faker()

    @classmethod
    def auth_user(cls, **overrides: Any) -> dict[str, Any]:
        payload = AuthPayload(
            email=cls._faker.email(domain="example.com"),
            password="TestPass123!",
            name=cls._faker.name(),
        )
        data = {
            "email": payload.email,
            "password": payload.password,
            "name": payload.name,
        }
        data.update(overrides)
        return data

    @classmethod
    def user(cls, **overrides: Any) -> dict[str, Any]:
        payload = UserPayload(
            email=cls._faker.email(domain="example.com"),
            name=cls._faker.name(),
        )
        data = {"email": payload.email, "name": payload.name, "role": payload.role}
        data.update(overrides)
        return data

    @classmethod
    def order(cls, user_id: int, **overrides: Any) -> dict[str, Any]:
        item = OrderItemPayload(
            product_id=cls._faker.bothify(text="PROD-####").upper(),
            quantity=cls._faker.random_int(min=1, max=3),
            price=round(cls._faker.pyfloat(min_value=10, max_value=200, right_digits=2), 2),
        )
        data = {
            "user_id": user_id,
            "items": [
                {
                    "product_id": item.product_id,
                    "quantity": item.quantity,
                    "price": item.price,
                }
            ],
        }
        data.update(overrides)
        return data

    @classmethod
    def payment(cls, order_id: int, amount: float, **overrides: Any) -> dict[str, Any]:
        payload = PaymentPayload(order_id=order_id, amount=amount, method="card")
        data = {
            "order_id": payload.order_id,
            "amount": payload.amount,
            "method": payload.method,
        }
        data.update(overrides)
        return data

    @classmethod
    def notification(cls, user_id: int, **overrides: Any) -> dict[str, Any]:
        payload = NotificationPayload(
            user_id=user_id,
            channel=cls._faker.random_element(["email", "sms", "push"]),
            message=cls._faker.sentence(nb_words=8),
        )
        data = {
            "user_id": payload.user_id,
            "channel": payload.channel,
            "message": payload.message,
        }
        data.update(overrides)
        return data
