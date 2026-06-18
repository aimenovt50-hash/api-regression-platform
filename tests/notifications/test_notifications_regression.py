import allure
import pytest

from src.data.factories.data_factory import DataFactory
from tests.helpers.api_assertions import assert_json_schema, assert_status
from tests.schemas.api_schemas import schema_from_contract


@pytest.mark.notifications
@pytest.mark.regression
@allure.story("Create notification")
def test_create_notification(authenticated_clients, registered_user):
    payload = DataFactory.notification(user_id=registered_user["user"]["user_id"])
    body = assert_status(authenticated_clients["notifications"].create(payload), 201)
    assert_json_schema(body, schema_from_contract("/notifications", "post", "201"))


@pytest.mark.notifications
@pytest.mark.regression
@allure.story("List notifications")
def test_list_notifications(authenticated_clients, registered_user):
    user_id = registered_user["user"]["user_id"]
    authenticated_clients["notifications"].create(DataFactory.notification(user_id=user_id))
    notifications = assert_status(authenticated_clients["notifications"].list_by_user(user_id), 200)
    assert len(notifications) >= 1


@pytest.mark.notifications
@pytest.mark.database
@allure.story("Mark notification read")
def test_mark_notification_read_database_validation(
    authenticated_clients,
    db_validator,
    registered_user,
):
    user_id = registered_user["user"]["user_id"]
    notification = assert_status(
        authenticated_clients["notifications"].create(DataFactory.notification(user_id=user_id)),
        201,
    )
    body = assert_status(
        authenticated_clients["notifications"].mark_read(notification["id"]),
        200,
    )
    assert body["is_read"] is True
    assert db_validator.notification_is_read(notification["id"]) is True
