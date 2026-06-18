import allure
import pytest

from src.data.factories.data_factory import DataFactory
from tests.helpers.api_assertions import assert_status


@pytest.mark.e2e
@pytest.mark.regression
@allure.feature("Order lifecycle")
@allure.story("Register → order → pay → notify")
def test_full_order_lifecycle(authenticated_clients, db_validator, registered_user):
    user_id = registered_user["user"]["user_id"]

    order = assert_status(
        authenticated_clients["orders"].create_order(DataFactory.order(user_id=user_id)),
        201,
    )
    payment = assert_status(
        authenticated_clients["payments"].create_payment(
            DataFactory.payment(order_id=order["id"], amount=order["total_amount"])
        ),
        201,
    )
    notification = assert_status(
        authenticated_clients["notifications"].create(
            DataFactory.notification(
                user_id=user_id,
                message=f"Payment {payment['id']} completed for order {order['id']}",
            )
        ),
        201,
    )
    assert_status(authenticated_clients["notifications"].mark_read(notification["id"]), 200)

    assert db_validator.order_status(order["id"]) == "paid"
    assert db_validator.payment_for_order(order["id"])["status"] == "completed"
    assert db_validator.notification_is_read(notification["id"]) is True
