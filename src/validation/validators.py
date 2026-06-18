from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, ValidationError
from jsonschema import validate as jsonschema_validate
from openapi_spec_validator import validate as validate_openapi_spec


class SchemaValidator:
    @staticmethod
    def validate(instance: Any, schema: dict[str, Any]) -> None:
        jsonschema_validate(instance=instance, schema=schema)

    @staticmethod
    def is_valid(instance: Any, schema: dict[str, Any]) -> bool:
        try:
            SchemaValidator.validate(instance, schema)
            return True
        except ValidationError:
            return False


class ContractValidator:
    @staticmethod
    def validate_openapi(contract_path: Path) -> None:
        with contract_path.open(encoding="utf-8") as handle:
            spec = yaml.safe_load(handle)
        validate_openapi_spec(spec)

    @staticmethod
    def _resolve_schema(spec: dict[str, Any], schema: dict[str, Any]) -> dict[str, Any]:
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            ref_schema = spec["components"]["schemas"][ref_name]
            return ContractValidator._resolve_schema(spec, deepcopy(ref_schema))

        resolved = deepcopy(schema)
        if "properties" in resolved:
            resolved["properties"] = {
                key: ContractValidator._resolve_schema(spec, value)
                for key, value in resolved["properties"].items()
            }
        if "items" in resolved and isinstance(resolved["items"], dict):
            resolved["items"] = ContractValidator._resolve_schema(spec, resolved["items"])
        return resolved

    @staticmethod
    def get_response_schema(
        contract_path: Path,
        path: str,
        method: str,
        status_code: str = "200",
    ) -> dict[str, Any]:
        with contract_path.open(encoding="utf-8") as handle:
            spec = yaml.safe_load(handle)
        operation = spec["paths"][path][method.lower()]
        response = operation["responses"][status_code]
        content = response["content"]["application/json"]
        return ContractValidator._resolve_schema(spec, content["schema"])

    @staticmethod
    def validate_response(
        contract_path: Path,
        path: str,
        method: str,
        payload: Any,
        status_code: str = "200",
    ) -> None:
        schema = ContractValidator.get_response_schema(contract_path, path, method, status_code)
        Draft202012Validator(schema).validate(payload)
