from __future__ import annotations

import hashlib
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import Depends, FastAPI, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.database import Notification, Order, OrderItem, Payment, User, get_db, init_db

app = FastAPI(title="Microservices Platform API", version="1.0.0")

TOKENS: dict[str, int] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def issue_token(user_id: int) -> str:
    token = secrets.token_urlsafe(24)
    TOKENS[token] = user_id
    return token


def get_current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    user_id = TOKENS.get(token)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive")
    return user


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=2)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserCreateRequest(BaseModel):
    email: EmailStr
    name: str
    role: str = "user"


class UserUpdateRequest(BaseModel):
    name: str | None = None
    role: str | None = None
    is_active: bool | None = None


class OrderItemRequest(BaseModel):
    product_id: str
    quantity: int = Field(ge=1)
    price: float = Field(gt=0)


class OrderCreateRequest(BaseModel):
    user_id: int
    items: list[OrderItemRequest] = Field(min_length=1)


class OrderStatusRequest(BaseModel):
    status: str


class PaymentCreateRequest(BaseModel):
    order_id: int
    amount: float = Field(gt=0)
    method: str


class NotificationCreateRequest(BaseModel):
    user_id: int
    channel: str
    message: str = Field(min_length=1)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/health")
def health():
    return {"status": "ok", "service": "platform-api"}


@app.post("/auth/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=payload.email, name=payload.name, password_hash=hash_password(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"user_id": user.id, "email": user.email, "name": user.name}


@app.post("/auth/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or user.password_hash != hash_password(payload.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = issue_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in": 3600,
        "user_id": user.id,
    }


@app.get("/auth/me")
def auth_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "is_active": current_user.is_active,
    }


@app.get("/users")
def list_users(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    users = db.query(User).all()
    return [
        {"id": u.id, "email": u.email, "name": u.name, "role": u.role, "is_active": u.is_active}
        for u in users
    ]


@app.post("/users", status_code=status.HTTP_201_CREATED)
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    if db.query(User).filter(User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="Email already exists")
    user = User(
        email=payload.email,
        name=payload.name,
        role=payload.role,
        password_hash=hash_password("TempPass123!"),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "is_active": user.is_active}


@app.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "is_active": user.is_active}


@app.patch("/users/{user_id}")
def update_user(
    user_id: int,
    payload: UserUpdateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name is not None:
        user.name = payload.name
    if payload.role is not None:
        user.role = payload.role
    if payload.is_active is not None:
        user.is_active = payload.is_active
    db.commit()
    db.refresh(user)
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "is_active": user.is_active}


@app.get("/orders")
def list_orders(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    orders = db.query(Order).all()
    return [
        {
            "id": o.id,
            "user_id": o.user_id,
            "status": o.status,
            "total_amount": o.total_amount,
            "items": [
                {"product_id": i.product_id, "quantity": i.quantity, "price": i.price} for i in o.items
            ],
        }
        for o in orders
    ]


@app.post("/orders", status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    total = sum(item.quantity * item.price for item in payload.items)
    order = Order(user_id=payload.user_id, status="created", total_amount=total)
    db.add(order)
    db.flush()
    for item in payload.items:
        db.add(
            OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
            )
        )
    db.commit()
    db.refresh(order)
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "items": [
            {"product_id": i.product_id, "quantity": i.quantity, "price": i.price} for i in order.items
        ],
    }


@app.get("/orders/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return {
        "id": order.id,
        "user_id": order.user_id,
        "status": order.status,
        "total_amount": order.total_amount,
        "items": [
            {"product_id": i.product_id, "quantity": i.quantity, "price": i.price} for i in order.items
        ],
    }


@app.patch("/orders/{order_id}/status")
def update_order_status(
    order_id: int,
    payload: OrderStatusRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    order = db.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return {"id": order.id, "status": order.status, "total_amount": order.total_amount}


@app.post("/payments", status_code=status.HTTP_201_CREATED)
def create_payment(payload: PaymentCreateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    order = db.get(Order, payload.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.payment:
        raise HTTPException(status_code=409, detail="Payment already exists")
    payment = Payment(order_id=payload.order_id, amount=payload.amount, method=payload.method, status="completed")
    order.status = "paid"
    db.add(payment)
    db.commit()
    db.refresh(payment)
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": payment.status,
    }


@app.get("/payments/{payment_id}")
def get_payment(payment_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    payment = db.get(Payment, payment_id)
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": payment.status,
    }


@app.get("/payments/order/{order_id}")
def get_payment_by_order(order_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    payment = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    return {
        "id": payment.id,
        "order_id": payment.order_id,
        "amount": payment.amount,
        "method": payment.method,
        "status": payment.status,
    }


@app.get("/notifications/user/{user_id}")
def list_notifications(user_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    notifications = db.query(Notification).filter(Notification.user_id == user_id).all()
    return [
        {
            "id": n.id,
            "user_id": n.user_id,
            "channel": n.channel,
            "message": n.message,
            "is_read": n.is_read,
        }
        for n in notifications
    ]


@app.post("/notifications", status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: NotificationCreateRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    user = db.get(User, payload.user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    notification = Notification(
        user_id=payload.user_id,
        channel=payload.channel,
        message=payload.message,
        is_read=False,
    )
    db.add(notification)
    db.commit()
    db.refresh(notification)
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "channel": notification.channel,
        "message": notification.message,
        "is_read": notification.is_read,
    }


@app.patch("/notifications/{notification_id}/read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    notification = db.get(Notification, notification_id)
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return {
        "id": notification.id,
        "user_id": notification.user_id,
        "channel": notification.channel,
        "message": notification.message,
        "is_read": notification.is_read,
    }
