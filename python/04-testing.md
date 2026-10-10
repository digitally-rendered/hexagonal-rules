# Testing (Python)

## 1. Absolute rules

- **Never skip.** `@pytest.mark.skip`, `pytest.skip()`, `@pytest.mark.xfail`
  are forbidden. Never comment out a test or assertion. Never `# type:
  ignore` a failing test. Never weaken an assertion to go green. The single
  exception is the Class B row of `shared/04` §5: an environment probe for
  a missing optional integration dependency (`pytest.skip(reason=…)` inside
  the probe helper only), which the CI job providing the dependency runs
  unskipped.
- A failing test has three resolutions: fix the code, fix the test, or
  escalate. There is no fourth.
- The ratchet counts `skipped_tests`; target 0.

## 2. Stacks by rung

| Rung | DB in tests | Notes |
|---|---|---|
| Level 0 (SQL DDD) | testcontainers for repository/integration tests; `AsyncMock(spec=Port)` for use cases | 100% coverage on new code |
| Levels 1–3 (schema-driven / Mongo) | `mongomock-motor` (not testcontainers, not a real Mongo) | ≥ 80% backend; aggregation operators differ in mocks, UUIDs stored as strings |

Always `poetry run pytest`. `pytest-asyncio` for every DB test.

## 3. Structure

```
tests/
├── conftest.py            shared fixtures: mock db, registry reset, test client
├── unit/                  no external deps (domain, use cases, models, factories)
├── integration/           repositories, schema-driven API, full flows
├── architecture/          AST fitness tests, enforcement-tooling agreement, collision checks
├── security/              invariants over every aggregate (ownership, authz)
├── schemathesis/          property-based fuzzing of the generated surface
├── mocks/ or fixtures/    JSON mock data, golden chunks, sample schemas
└── helpers/
```

`pytest tests/unit tests/integration` is **not** "the backend passes";
schemathesis and architecture directories are collected only by a bare
`pytest`.

## 4. Patterns

- Registry reset in an autouse fixture.
- Versioned CRUD: create → `record_version == 1`, `entity_id` set,
  `deleted_at is None`; delete → tombstone `record_version == 2`,
  `get` returns `None`.
- Use cases: mock every secondary port; assert calls and the response DTO.
- In-memory adapters for full-workflow integration tests of the core.
- **Contract tests** run against every implementation of a port (SQL, Mongo,
  in-memory); `isinstance(impl, Port)` for Protocols.
- Technology adapters are tested separately, asserting on the stored model.
- Domain: entity behaviour, factory methods, invariants, events raised.
- Builders/factories for test data.

## 5. Schemathesis

- Fuzzes every generated endpoint with positive, negative and stateful cases.
  It is what justifies calling the generated layer correct by construction.
- Every new generated surface (a new factory that produces endpoints) is
  registered in the fuzzing suite's conftest in the same change.
- Checks run only when listed in `ENABLED_CHECKS`; registration via
  `@schemathesis.check` alone does nothing when `checks=` is passed. The
  authoritative list includes the library's hex checks:
  `entity_id_is_valid_uuid`, `record_version_starts_at_one`,
  `audit_timestamps_present`, `no_deleted_at_on_active_documents`, plus
  response schema/status/content-type/headers conformance and
  `negative_data_rejection`. `ignored_auth` is excluded by design (auth is
  overridden for the fuzzing app; it belongs to `tests/security/`).
- Failures are baselined in `check_baseline.json` as a ratchet; systemic
  entries name the generator defect, match narrowly, and may only be deleted.
  Regenerate only deliberately, same commit, reason in the message.
- Build the fuzzing app by registering generated routers **before** handing
  the router to a fresh app.

## 6. Architecture fitness tests

- AST walk of the real tree; empty allowlist for core→adapters; explicit,
  commented adapter→adapter allowlist that fails on stale entries; core must
  not import `fastapi`; Motor-in-core allowlist tracked to zero.
- Enforcement tooling agreement: the lint plugin, the drift script, and the
  fitness tests must agree on what counts as a violation.
- Schema/collection collision test resolves ownership through the registry
  accessor (`x-collection` aware).
- Drift tests between sibling implementations; prompt snapshot tests over
  golden chunks; guard tests validated by re-introducing the defect.

## 7. Verification protocol

The tiers are `shared/06` §12. Python commands per tier: ruff and mypy on
the changed file (Tier 1); `poetry run pytest <file>` (Tier 2); bare
`poetry run pytest` with coverage (Tier 3); the handoff checks plus
generated endpoints visible in `/docs` and `grep -r "skip\|xfail" tests/`
finding nothing new (Tier 4).

## 8. Slice tests (the Python equivalents of `shared/07` §2)

| `shared/07` row | What proves it in Python |
|---|---|
| B1 schema | `SchemaRegistry` loads `schemas/<entity>.json`; the generated Create/Update/Document models validate a sample payload and raise `ValidationError` on an invalid one; `get_owner_field` resolves; the schema/collection collision test passes |
| B1 classical | dataclass entity, value objects, factory: unit tests on factory, invariants, `_events`; the AST fitness test finds no framework import |
| B2 versioned | the versioned CRUD contract tests against `mongomock-motor`: create → v1; update → v2, new `id`; delete → tombstone; `get` after delete → `None`; `list_latest_active` drops tombstones and superseded versions |
| B2 relational | SQLAlchemy model + Alembic migration: upgrade → downgrade → upgrade; `alembic revision --autogenerate` produces an empty migration; every column in the migration and every `_to_domain` field in both; repository integration test against testcontainers |
| B3 ports | use-case tests with `AsyncMock(spec=Port)`; `isinstance(impl, Port)` for every implementation of a `runtime_checkable` Protocol; the contract test over every adapter |
| B4 primary adapter | the generated router registers; the endpoint appears in `/docs` with all five operations (or the view); owner 200, stranger 403 (this application's posture), missing 404 |
| B5 composition root | the container resolves the new use case; a request through the real app reaches the handler (routes added after `include_router` never mount) |
| C ladder | `tests/unit`, `tests/integration`, `tests/architecture`, `tests/security`, `tests/schemathesis`, the drift ratchet; coverage at the repository's committed threshold |
| D frontend (the schema-driven application's React side) | the type-generation script re-run and diffed (the drift check, `shared/02` §1); adapter tests with MSW; hook tests with a stub port and no `useApiClient()` in a dependency array; an `axe` assertion in every component test file; `npm run build` passes |
| F end to end | Playwright: page objects; one `test.describe.serial` full workflow journey per feature; axe-core WCAG 2.1 AA per new page; `test-map.json` updated for changed-only runs |
