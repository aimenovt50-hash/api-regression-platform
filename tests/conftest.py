from __future__ import annotations

import os
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path

import allure
import pytest
import requests

from src.clients.http_client import HttpClient
from src.clients.service_clients import (
    AuthClient,
    NotificationsClient,
    OrdersClient,
    PaymentsClient,
    UsersClient,
)
from src.config.settings import EnvironmentConfig, get_environment_config
from src.data.factories.data_factory import DataFactory
from src.db.database_validator import DatabaseValidator

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def pytest_addoption(parser):
    parser.addoption("--env", action="store", default=None, help="Target environment")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


@pytest.fixture(scope="session")
def env_name(pytestconfig) -> str:
    return pytestconfig.getoption("--env") or "local"


@pytest.fixture(scope="session")
def api_server(env_name: str):
    if env_name != "local":
        yield None
        return

    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    db_path = PROJECT_ROOT / f"platform_{uuid.uuid4().hex[:8]}.db"

    os.environ["API_BASE_URL"] = base_url
    os.environ["PLATFORM_DB_PATH"] = str(db_path)
    os.environ["DATABASE_URL"] = f"sqlite:///{db_path.as_posix()}"
    get_environment_config.cache_clear()

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=PROJECT_ROOT,
        env={**os.environ},
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    for _ in range(40):
        if process.poll() is not None:
            raise RuntimeError("Mock platform API exited early")
        try:
            response = requests.get(f"{base_url}/health", timeout=1)
            if response.status_code == 200:
                break
        except requests.RequestException:
            time.sleep(0.25)
    else:
        process.terminate()
        raise RuntimeError("Mock platform API failed to start within timeout")

    yield base_url

    process.terminate()
    process.wait(timeout=5)
    try:
        db_path.unlink(missing_ok=True)
    except PermissionError:
        pass


@pytest.fixture(scope="session")
def env_config(env_name: str, api_server) -> EnvironmentConfig:
    return get_environment_config(env_name)


@pytest.fixture(autouse=True)
def allure_environment(env_config: EnvironmentConfig):
    allure.dynamic.epic("Microservices Platform")
    allure.dynamic.feature(env_config.name)
    allure.dynamic.parameter("environment", env_config.name)


@pytest.fixture()
def http_client(env_config: EnvironmentConfig) -> HttpClient:
    return HttpClient(base_url=env_config.api_base_url)


@pytest.fixture()
def auth_client(http_client: HttpClient) -> AuthClient:
    return AuthClient(http_client)


@pytest.fixture(scope="session")
def db_validator(env_config: EnvironmentConfig, api_server) -> DatabaseValidator:
    db_path = os.environ.get("PLATFORM_DB_PATH", str(PROJECT_ROOT / "platform.db"))
    validator = DatabaseValidator(f"sqlite:///{Path(db_path).as_posix()}")
    yield validator
    validator.engine.dispose()


@pytest.fixture()
def registered_user(auth_client: AuthClient):
    payload = DataFactory.auth_user()
    register = auth_client.register(payload)
    assert register.status_code == 201
    login = auth_client.login({"email": payload["email"], "password": payload["password"]})
    assert login.status_code == 200
    token = login.json()["access_token"]
    return {
        "payload": payload,
        "user": register.json(),
        "token": token,
    }


@pytest.fixture()
def authenticated_clients(env_config: EnvironmentConfig, registered_user):
    client = HttpClient(env_config.api_base_url, token=registered_user["token"])
    return {
        "auth": AuthClient(client),
        "users": UsersClient(client),
        "orders": OrdersClient(client),
        "payments": PaymentsClient(client),
        "notifications": NotificationsClient(client),
    }
