from __future__ import annotations

from pathlib import Path

from src.config.settings import PROJECT_ROOT
from src.validation.validators import ContractValidator


def schema_from_contract(path: str, method: str, status_code: str = "200") -> dict:
    contract_path = PROJECT_ROOT / "contracts/openapi.yaml"
    return ContractValidator.get_response_schema(contract_path, path, method, status_code)
