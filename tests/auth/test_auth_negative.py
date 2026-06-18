import allure
import pytest

from src.data.factories.data_factory import DataFactory


@pytest.mark.auth
@pytest.mark.negative
@pytest.mark.regression
@allure.story("Invalid credentials")
def test_login_with_wrong_password(auth_client, registered_user):
    payload = registered_user["payload"]
    response = auth_client.login({"email": payload["email"], "password": "WrongPass123!"})
    assert response.status_code == 401


@pytest.mark.auth
@pytest.mark.negative
@pytest.mark.regression
@allure.story("Duplicate registration")
def test_register_duplicate_email(auth_client):
    payload = DataFactory.auth_user()
    assert auth_client.register(payload).status_code == 201
    duplicate = auth_client.register(payload)
    assert duplicate.status_code == 409


@pytest.mark.auth
@pytest.mark.negative
@pytest.mark.regression
@allure.story("Unauthorized access")
def test_auth_me_without_token(http_client):
    response = http_client.get("/auth/me")
    assert response.status_code == 401
