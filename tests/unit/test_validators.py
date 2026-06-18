from src.config.settings import PROJECT_ROOT
from src.validation.validators import ContractValidator, SchemaValidator


def test_schema_validator_accepts_valid_payload():
    schema = {"type": "object", "required": ["id"], "properties": {"id": {"type": "integer"}}}
    SchemaValidator.validate({"id": 1}, schema)


def test_openapi_contract_loads():
    ContractValidator.validate_openapi(PROJECT_ROOT / "contracts/openapi.yaml")
