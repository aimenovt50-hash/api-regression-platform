import allure
import pytest

from src.data.factories.data_factory import DataFactory


@pytest.mark.users
@pytest.mark.negative
@pytest.mark.regression
@allure.story("Unauthorized list")
def test_list_users_without_token(http_client):
    assert http_client.get("/users").status_code == 401


@pytest.mark.users
@pytest.mark.negative
@pytest.mark.regression
@allure.story("Missing user")
def test_get_missing_user(authenticated_clients):
    assert authenticated_clients["users"].get_user(999999).status_code == 404
