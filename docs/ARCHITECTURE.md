# Architecture

## Test pyramid

```
smoke/          → health + critical paths (< 1 min)
regression/     → domain happy paths + DB checks
negative/       → 401/404/409/422 boundaries
contract/       → OpenAPI spec parity
e2e/            → cross-domain business flows
unit/           → framework utilities (validators, config)
```

## Single source of truth for schemas

Response schemas are derived from `contracts/openapi.yaml` via `schema_from_contract()`.
Avoid duplicating JSON Schema in Python — contract drives validation.

## Client layer

- `HttpClient` — retries, timeout from `config/settings.yaml`, Allure attachments
- `service_clients.py` — domain-specific API surface
- Function-scoped clients prevent token/session leakage under `pytest-xdist`

## Database validation

`DatabaseValidator` validates post-conditions in SQLite after API mutations.
Table names are whitelisted; prefer typed helpers (`order_status`, `user_name`).

## Local runtime

`tests/conftest.py` boots mock platform API (`app/main.py`) for `local` env.
For staging, point `API_BASE_URL` to real services and disable subprocess boot.

## CI strategy

| Job | Trigger | Scope |
|-----|---------|-------|
| smoke | PR | `-m smoke` |
| regression | main | full suite + parallel |
| lint | PR/main | ruff on `src`, `tests`, `app` |
