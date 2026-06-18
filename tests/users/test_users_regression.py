import allure
import pytest

from src.data.factories.data_factory import DataFactory
from tests.helpers.api_assertions import assert_json_schema, assert_status
from tests.schemas.api_schemas import schema_from_contract


@pytest.mark.users
@pytest.mark.regression
@allure.story("Create user")
def test_create_user(authenticated_clients):
    body = assert_status(authenticated_clients["users"].create_user(DataFactory.user()), 201)
    assert_json_schema(body, schema_from_contract("/users", "post", "201"))


@pytest.mark.users
@pytest.mark.regression
@allure.story("List users")
def test_list_users(authenticated_clients, registered_user):
    users = assert_status(authenticated_clients["users"].list_users(), 200)
    assert any(user["email"] == registered_user["payload"]["email"] for user in users)


@pytest.mark.users
@pytest.mark.database
@allure.story("Update user")
def test_update_user_database_validation(authenticated_clients, db_validator, registered_user):
    user_id = registered_user["user"]["user_id"]
    new_name = "Updated QA User"
    assert_status(authenticated_clients["users"].update_user(user_id, {"name": new_name}), 200)
    assert db_validator.user_name(user_id) == new_name
