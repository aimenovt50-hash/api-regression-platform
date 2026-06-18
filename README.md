# API Regression Platform

Automated regression suite for a microservices platform. Designed as a **senior API test platform** with domain clients, contract-first validation, DB post-conditions, negative/security coverage, and a CI smoke gate.

## Principles (senior-level)

| Principle | Implementation |
|-----------|----------------|
| **Contract-first** | OpenAPI is the single source of response schemas |
| **Layered clients** | HttpClient → domain clients → assertions |
| **Test isolation** | Function-scoped clients, separate token per test |
| **Multi-layer validation** | JSON Schema + OpenAPI + SQLite post-checks |
| **Observable API calls** | Allure attachments on failed requests |

## Architecture

```
app/                     # mock platform (FastAPI + SQLite)
contracts/openapi.yaml   # API contract
src/clients/             # HTTP + domain clients
src/validation/          # schema + contract validators
src/db/                  # database validators
tests/
  smoke/                 # health gate
  auth|users|orders|...  # domain regression
  negative/              # 401/404/409
  contract/              # OpenAPI parity
  e2e/                   # cross-domain flows
docs/ARCHITECTURE.md
```

## Domains

Authentication · Users · Orders · Payments · Notifications

## Quick start

```powershell
cd d:\QA\api-regression-platform
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
pytest --env=local
```

## Running by level

```powershell
pytest -m smoke --env=local              # PR gate
pytest -m regression --env=local         # happy path by domain
pytest -m negative --env=local           # security/boundary
pytest -m contract --env=local           # OpenAPI parity
pytest -m e2e --env=local                # order lifecycle
pytest -m database --env=local           # DB post-validation
pytest -n auto --env=local               # parallel
```

## Validation layers

1. **Status assertions** — `tests/helpers/api_assertions.py`
2. **JSON Schema** — derived from OpenAPI via `schema_from_contract()`
3. **Contract testing** — `ContractValidator.validate_response()`
4. **Database validation** — `DatabaseValidator` after mutations

## E2E flow

`tests/e2e/test_order_lifecycle.py`: register → order → pay → notify → DB verify

## CI/CD

| Workflow | Purpose |
|----------|---------|
| `ci.yml` | smoke (PR) + full regression (main), parallel, Allure |
| `lint.yml` | ruff on `app`, `src`, `tests` |

## Staging

Update `config/environments/staging.yaml` and CI secrets. The local mock API is not started for non-local URLs.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.
