import allure
import pytest

from tests.helpers.api_assertions import assert_status


@pytest.mark.smoke
@allure.story("Platform health")
def test_health(http_client):
    body = assert_status(http_client.get("/health"), 200)
    assert body["status"] == "ok"
