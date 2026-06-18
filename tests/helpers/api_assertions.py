from __future__ import annotations

from typing import Any

import requests

from src.validation.validators import ContractValidator, SchemaValidator


def assert_status(response: requests.Response, expected: int | tuple[int, ...]) -> dict[str, Any]:
    codes = (expected,) if isinstance(expected, int) else expected
    assert response.status_code in codes, (
        f"Expected {codes}, got {response.status_code}: {response.text}"
    )
    return response.json()


def assert_json_schema(body: dict[str, Any], schema: dict[str, Any]) -> None:
    SchemaValidator.validate(body, schema)


def assert_contract_response(
    contract_path,
    path: str,
    method: str,
    body: dict[str, Any],
    status_code: str,
) -> None:
    ContractValidator.validate_response(contract_path, path, method, body, status_code)
