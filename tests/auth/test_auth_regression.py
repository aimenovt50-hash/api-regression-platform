import allure
import pytest

from tests.helpers.api_assertions import assert_json_schema, assert_status
from tests.schemas.api_schemas import schema_from_contract


@pytest.mark.auth
@pytest.mark.regression
@allure.story("Register user")
def test_register_user(auth_client):
    from src.data.factories.data_factory import DataFactory

    response = auth_client.register(DataFactory.auth_user())
    body = assert_status(response, 201)
    assert_json_schema(body, schema_from_contract("/auth/register", "post", "201"))


@pytest.mark.auth
@pytest.mark.regression
@allure.story("Login user")
def test_login_user(auth_client, registered_user):
    payload = registered_user["payload"]
    response = auth_client.login({"email": payload["email"], "password": payload["password"]})
    body = assert_status(response, 200)
    assert_json_schema(body, schema_from_contract("/auth/login", "post"))


@pytest.mark.auth
@pytest.mark.smoke
@allure.story("Current user profile")
def test_auth_me(authenticated_clients, registered_user):
    response = authenticated_clients["auth"].me()
    body = assert_status(response, 200)
    assert body["email"] == registered_user["payload"]["email"]
