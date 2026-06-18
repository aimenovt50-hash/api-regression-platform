from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = PROJECT_ROOT / "config"
ENVIRONMENTS_DIR = CONFIG_DIR / "environments"


class RetryConfig(BaseModel):
    max_attempts: int = 3
    backoff_factor: float = 0.5


class GlobalSettings(BaseModel):
    name: str = "microservices-platform"
    timeout_seconds: int = 15
    retry: RetryConfig = Field(default_factory=RetryConfig)


class EnvironmentCredentials(BaseModel):
    admin_email: str = ""
    admin_password: str = ""


class EnvironmentConfig(BaseModel):
    name: str
    api_base_url: str
    database_url: str
    contract_path: str = "contracts/openapi.yaml"
    credentials: EnvironmentCredentials = Field(default_factory=EnvironmentCredentials)


class RuntimeSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    env: str = Field(default="local", alias="ENV")
    api_base_url: str | None = Field(default=None, alias="API_BASE_URL")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    contract_path: str | None = Field(default=None, alias="CONTRACT_PATH")


def _load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


@lru_cache
def get_global_settings() -> GlobalSettings:
    load_dotenv(PROJECT_ROOT / ".env")
    return GlobalSettings.model_validate(_load_yaml(CONFIG_DIR / "settings.yaml"))


@lru_cache
def get_environment_config(env_name: str | None = None) -> EnvironmentConfig:
    load_dotenv(PROJECT_ROOT / ".env")
    runtime = RuntimeSettings()
    selected_env = env_name or runtime.env
    env_path = ENVIRONMENTS_DIR / f"{selected_env}.yaml"
    if not env_path.exists():
        raise FileNotFoundError(f"Environment '{selected_env}' not found")
    config = EnvironmentConfig.model_validate(_load_yaml(env_path))
    if runtime.api_base_url:
        config.api_base_url = runtime.api_base_url.rstrip("/")
    if runtime.database_url:
        config.database_url = runtime.database_url
    if runtime.contract_path:
        config.contract_path = runtime.contract_path
    return config
