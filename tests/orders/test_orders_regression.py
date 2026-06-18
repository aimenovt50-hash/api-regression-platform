import allure
import pytest

from src.data.factories.data_factory import DataFactory
from tests.helpers.api_assertions import assert_json_schema, assert_status
from tests.schemas.api_schemas import schema_from_contract


@pytest.mark.orders
@pytest.mark.regression
@allure.story("Create order")
def test_create_order(authenticated_clients, registered_user):
    payload = DataFactory.order(user_id=registered_user["user"]["user_id"])
    body = assert_status(authenticated_clients["orders"].create_order(payload), 201)
    assert_json_schema(body, schema_from_contract("/orders", "post", "201"))


@pytest.mark.orders
@pytest.mark.regression
@allure.story("Get order by id")
def test_get_order(authenticated_clients, registered_user):
    created = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    body = assert_status(authenticated_clients["orders"].get_order(created["id"]), 200)
    assert body["id"] == created["id"]


@pytest.mark.orders
@pytest.mark.database
@allure.story("Update order status")
def test_update_order_status_database_validation(authenticated_clients, db_validator, registered_user):
    order = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    assert_status(authenticated_clients["orders"].update_status(order["id"], "processing"), 200)
    assert db_validator.order_status(order["id"]) == "processing"
