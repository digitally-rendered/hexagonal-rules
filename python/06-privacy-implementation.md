# Privacy layering: Python implementation notes

How the eight layers of `shared/08-data-privacy-layering.md` land in a
Python backend (FastAPI, Pydantic v2, SQLAlchemy 2 or Motor). Same table
shape as `typescript/11` and `go/06`; the mechanism is the same, the idiom
differs. Ownership scoping as implemented by the schema-driven framework is
in `python/02` §14.

| Layer | Implementation |
|---|---|
| L0 storage tiers | `pydantic-settings` model loaded once in `config.py`; nothing reads `os.environ` elsewhere; secrets from the environment or a keyring, never from a committed file; `gitleaks` (or `detect-secrets`) in pre-commit; private directories outside the repository. Check: a fitness test finds `os.environ` only in `config.py` |
| L1 classification | `core/domain/classification.py`: `REGISTRY: Mapping[FieldId, frozenset[Tier]]` with a `strictest(tags)` resolver; a test enumerates persisted fields (SQLAlchemy mapped columns or registry schema properties) and fails on any without an entry |
| L2 audience / privilege | one `classify(participants)` function in one module; every consumer imports it; the AST fitness test fails on a second role table (a module-level mapping of role names outside that module) |
| L3 ownership scoping | applied in `EndpointFactory` from `x-owner-field` resolved once per schema through the registry accessor; fail-closed branches; `tests/security/` parametrised over every schema in the registry with two least-privileged principals (`python/02` §14) |
| L4 ReBAC | `AuthorizationPort` (`Protocol`) in `core/ports/` or `domain/ports/`; `AuthorizationService` with the priority chain in the domain; repositories take the principal and apply isolation in the query (`select(...).where(...)` or the Mongo filter), never post-filter; per-request relationship cache on `request.state` via a FastAPI dependency |
| L5 delegation | `Principal` dataclass with `is_obo`, `agent_id`, `obo_scopes`, built by the auth dependency from token-exchange claims; scope intersection in the authorization service; admin override never inherited by a delegated principal. Check: a test asserts an OBO principal with admin claims cannot reach a row its delegating user cannot |
| L6 consent | `ConsentRecord` frozen dataclass; repository port with `append` and `list_by_user` only (no update, no delete); `require_active_consent(principal)` as a FastAPI dependency or a `@registry.guard` on every write operation that persists personal data. Check: a test enumerates write operations touching classified fields and asserts the guard is installed on each |
| L7 encryption | `KeyManagementPort` in `core/ports/` (or `application/ports/secondary/`); envelope codec in `adapters/crypto/envelope.py` using `cryptography`'s `AESGCM` with the header as associated data; encrypted columns via a SQLAlchemy `TypeDecorator` (`EncryptedString`) or a Motor codec/`model_validator` on the document base so repositories are unaware; request-scoped DEK cache in a `contextvars.ContextVar`, never persisted or logged; blind index as an HMAC-SHA256 column. Check: a test writes through the repository and asserts the raw row holds ciphertext and the blind index, never the plaintext |
| L8 audit | two append-only tables or collections behind `AuditStorePort`; a test drives a real request through the FastAPI app (`httpx.AsyncClient`) and asserts the audit row exists with actor, action and target; the evidence exporter reads only (`shared/08` §10) |

Rules that follow:

- The domain never imports `cryptography`, `sqlalchemy`, `motor`, `fastapi`
  or `jose`; encryption, authorization and audit are absorbed at adapter or
  dependency boundaries so entities, use cases and controllers are
  unchanged. Check: the AST fitness test of `python/04` §6.
- Denials do not distinguish "does not exist" from "not allowed" at the
  port; the transport picks the project posture once (`shared/01` §5).
- Every check in the table is a pytest test under `tests/security/` or
  `tests/architecture/`, collected by a bare `pytest`, never only by the
  unit directory.
