from pathlib import Path

import allure
import pytest

from src.config.settings import PROJECT_ROOT
from src.data.factories.data_factory import DataFactory
from src.validation.validators import ContractValidator
from tests.helpers.api_assertions import assert_contract_response, assert_status


@pytest.mark.contract
@pytest.mark.regression
@allure.feature("Contract Testing")
def test_openapi_contract_is_valid(env_config):
    ContractValidator.validate_openapi(PROJECT_ROOT / env_config.contract_path)


@pytest.mark.contract
@pytest.mark.regression
@allure.feature("Contract Testing")
def test_auth_login_contract(auth_client, registered_user):
    contract_path = PROJECT_ROOT / "contracts/openapi.yaml"
    payload = registered_user["payload"]
    body = assert_status(auth_client.login({"email": payload["email"], "password": payload["password"]}), 200)
    assert_contract_response(contract_path, "/auth/login", "post", body, "200")


@pytest.mark.contract
@pytest.mark.regression
@allure.feature("Contract Testing")
def test_order_create_contract(authenticated_clients, registered_user):
    contract_path = PROJECT_ROOT / "contracts/openapi.yaml"
    body = assert_status(
        authenticated_clients["orders"].create_order(
            DataFactory.order(user_id=registered_user["user"]["user_id"])
        ),
        201,
    )
    assert_contract_response(contract_path, "/orders", "post", body, "201")
