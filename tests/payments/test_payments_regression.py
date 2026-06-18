import allure
import pytest

from src.data.factories.data_factory import DataFactory
from tests.helpers.api_assertions import assert_json_schema, assert_status
from tests.schemas.api_schemas import schema_from_contract


@pytest.mark.payments
@pytest.mark.regression
@allure.story("Create payment")
def test_create_payment(authenticated_clients, registered_user):
    order = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    body = assert_status(
        authenticated_clients["payments"].create_payment(
            DataFactory.payment(order_id=order["id"], amount=order["total_amount"])
        ),
        201,
    )
    assert_json_schema(body, schema_from_contract("/payments", "post", "201"))


@pytest.mark.payments
@pytest.mark.database
@allure.story("Payment side effects")
def test_payment_updates_order_status(authenticated_clients, db_validator, registered_user):
    order = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    payment = assert_status(
        authenticated_clients["payments"].create_payment(
            DataFactory.payment(order_id=order["id"], amount=order["total_amount"])
        ),
        201,
    )
    assert payment["status"] == "completed"
    assert db_validator.order_status(order["id"]) == "paid"


@pytest.mark.payments
@pytest.mark.regression
@allure.story("Get payment by order")
def test_get_payment_by_order(authenticated_clients, registered_user):
    order = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    created = assert_status(
        authenticated_clients["payments"].create_payment(
            DataFactory.payment(order_id=order["id"], amount=order["total_amount"])
        ),
        201,
    )
    body = assert_status(authenticated_clients["payments"].get_payment_by_order(order["id"]), 200)
    assert body["id"] == created["id"]
