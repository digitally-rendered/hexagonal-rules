# The schema-driven hexagon (TypeScript / Node)

Levels 2–3 of the ladder in TypeScript. Source: [Syntact](https://github.com/digitally-rendered/Syntact), the
TypeScript implementation of the same hexagon as slip-stream and
stellar-drive, currently in flight; these rules follow its design and will
be confirmed against its test paths when it ships. Mirrors
`python/02-schema-driven-framework.md` and `go/01-go-hexagonal.md`.

Stack: Node ≥ 22 (verified on Bun), TypeScript strict with
`exactOptionalPropertyTypes`, `noUncheckedIndexedAccess`,
`verbatimModuleSyntax`, ESM only; Ajv 2020-12 + formats; Hono on Web
Standard Request/Response (Fastify behind the same contract); the Mongo
driver; Kysely for SQL; pino; Vitest; fast-check; dependency-cruiser and
`eslint-plugin-boundaries`.

## 1. Packages and levels (monorepo as rung-1 enforcement)

```
packages/
  core              L0–L3  errors, model, util | query, event | schema, ports | registry, container, service, executor
  adapter-memory    L4     append-only in-memory repository + schema store (production-grade; the test double IS the reference)
  adapter-mongo     L4     repository, schema store, audit store, indexes, query translation, change streams
  adapter-sql       L4     Kysely repository (Postgres, MySQL, SQLite), migrations
  adapter-webhook   L4     HMAC dispatcher, retry/backoff, dead-letter
  adapter-streaming L4     bridge + memory/kafka/nats/redis streamers
  adapter-policy    L4     inline rules, OPA wasm, remote OPA
  adapter-telemetry L4     OpenTelemetry instrumentor, exporter
  http              L5     transport-neutral driving layer: operation handlers, middleware contract, OpenAPI, schema/audit/webhook APIs
  adapter-hono      L5     Hono bindings
  adapter-fastify   L5     Fastify bindings over the same contract
  adapter-graphql   L5     SDL/resolvers/subscriptions; runs the executor
  codegen           L5     JSON Schema → TS types, typed wrappers, OpenAPI, SDL, SDK, override stubs
  mcp               L5     tool server exposing schema/query/codegen tools
  engine            L6     composition root, config, lifecycle, storage routing
  testing           L6     test engine, data generator, lifecycle runner, event capture, hex checks, port contract suites
  cli               L7     init | run | schema | generate | migrate | mcp | bench
examples/           L7     reference consumer embedding the engine
benchmarks/         L7     micro + HTTP load + compat
```

- A package imports only lower levels; the workspace dependency graph
  enforces it across packages and dependency-cruiser enforces sub-levels
  inside `core`. `core` has **zero** runtime dependencies beyond the JSON
  Schema validator and semver; a test asserts the allowlist.
- `no-restricted-imports` forbids any HTTP framework, driver, or GraphQL
  library in `core`.

## 2. Core contracts

- **Document**: `AuditFields` (per-version `id`, stable `entity_id`,
  `schema_name`, `schema_version`, `record_version`, timestamps,
  `deleted_at`, `*_by`) + `data`. `AUDIT_FIELD_NAMES` is one tuple;
  `etagOf(doc)` is one function (`W/"<entity_id>:<record_version>"`).
- **DomainError** with a closed `ErrorCode` union and **one**
  `HTTP_STATUS` table (shared table plus `PRECONDITION_FAILED` 412,
  `RATE_LIMITED` 429, `SERVICE_UNAVAILABLE` 503); constructors per code;
  `HookAbort` for pre-hooks; `toProblem()` / `toEnvelope()` body builders.
- **Events**: `OPERATIONS` (8) × pre/post = 16 `LifecycleEvent`s; bus with
  global-before-specific order within each stage, pre aborts on first
  throw, post logs and never throws.
- **RequestContext**: operation, schema name and resolved version, channel
  (`rest | graphql | cli | mcp | internal`), request id, principal,
  entity id and hydrated entity, validated data, query, pagination,
  `if_match`/`if_none_match`, result, bulk state, `extras`, `AbortSignal`.
  It is the command; every channel builds one and calls the executor.
- **Schema**: envelope `{name, version, schema, storage?, collection?,
  indexes?, extensions?}`; the loader also accepts the bare-schema form
  (`title`/`version` at root) and normalises it. `CompiledSchema` carries
  the three Ajv validators (document, create, update), the flattened field
  list, the queryable allowlist, the owner field, and the single collection
  accessor. Unknown `x-*` extensions fail closed (`SCHEMA_INVALID`).
- **Query DSL**: one operator authority (18 operators; `_startswith`
  canonical with `_starts_with` accepted as an alias), `FilterNode` AST,
  `parseWhere` (stable key order, scalar-only `_eq`, depth limit),
  `validateQuery` (allowlist + types, **always** called by the executor),
  `parseSort` with a stable tiebreak, keyset cursors, and a pure
  reference `evaluate(filter, doc)` used by the memory adapter and as the
  differential oracle for every translator.
- **Ports**: `Repository` (create, findById, findVersion, history, list,
  count, update with CAS, delete, bulk ×3, ensureIndexes, `capabilities`),
  `Service`, `PolicyEvaluator`, `WebhookDispatcher`, `EventStreamer`,
  `AuditStore`, `SchemaStore`, `Clock`, `IdMinter`. A `REPOSITORY_METHODS`
  tuple plus passthrough decorator classes; a test proves every method
  forwards.

## 3. Registry, container, executor

- `FunctionRegistry` fluent API (`handler`, `guard`, `validate`,
  `transform`, `on`, `publish`, `storage`) with scope specificity scoring
  (version+channel 4, channel 3, version 2, universal 1; mismatch
  excluded), stable ordering, and `'*'` schema. Decorator syntax is not the
  primary surface.
- `Container` resolution: request override → schema-specific →
  storage-routed default → generated (through an injected service factory
  so the container never imports the generic service). Convention-based
  `discover()` (`<name>.repository.ts` exporting `<Pascal>Repository`,
  etc.) swallows only module-not-found.
- `OperationExecutor.run(ctx)` is the one pipeline for every channel:
  handler override → hydrate (missing or tombstoned is **always** 404
  before any hook; existing-but-not-owned is 403 or 404 by one
  project-wide posture) → guards → validators → before-transforms →
  re-validate data → `pre_*` → preconditions (`If-Match` → 412) → service
  → after-transforms → `post_*` (logged, never alters the response).
  Bulk fires one `pre_bulk_*`/`post_bulk_*` and runs per-item hooks on
  cloned contexts.
- Built-in ownership guard from `x-owner-field` (default `created_by`,
  `null` + reason = shared): privileged roles see all; others only their
  rows; no id → match-nothing on list; PATCH/DELETE check before write.

## 4. Persistence

- Append-only on every adapter; `list` = latest-active **then** filter,
  sort, paginate (the resurrection case is a named contract test).
- Optimistic concurrency by construction: every update or delete inserts
  `record_version + 1` and relies on the unique `(entity_id,
  record_version)` index; duplicate key → `CONFLICT`; `If-Match` mismatch
  → 412 before the write.
- Every audit field is written on every row, including `schema_version`
  and `*_by`.
- User-declared unique indexes apply to latest-active rows only (partial
  index + application check).
- Update runs inside one transaction on SQL; unknown operators throw, never
  compile to a tautology.
- The memory adapter is production-grade and runs the same contract suite
  as Mongo and SQL.
- UUIDs are stored as strings (v7); the normalisation rule is in
  `shared/03` §6.

## 5. Validation lifecycle

Every request passes these gates in order; each names its error and its
test:

| # | Gate | Failure |
|---|---|---|
| 0 | schema file load: envelope shape, name regex, semver, object type, meta-schema compile, audit fields stripped, `x-*` fail-closed | `SCHEMA_INVALID` |
| 1 | transport parse: method, path → schema name, UUID format, JSON body, pagination params | 400 |
| 2 | schema version resolution (`X-Schema-Version` / `?version`) | 404 |
| 3 | auth (JWT; never a trusted header by default) | 401 |
| 4 | rate limit | 429 + `Retry-After` |
| 5 | `where` parse then `validateQuery` against the allowlist | 400 with details |
| 6 | body validation against the **requested** version's variant, `additionalProperties:false`, defaults, formats | 422 with `field` from `instancePath` |
| 7 | hydration: exists and not a tombstone | 404 |
| 8 | guards and policy | 403 (policy evaluator failure → 503) |
| 9 | custom validators | 422 / 409 |
| 10 | before-transforms, then **re-validate** | 422 |
| 11 | `pre_*` hooks may abort | hook's code |
| 12 | `If-Match` vs `etagOf(entity)` | 412 |
| 13 | read-time migration of the hydrated entity | 500 if the chain is missing, logged |
| 14 | repository CAS insert | 409 |
| 15 | unique user indexes on latest-active | 409 with field |
| 16 | full-document validation of the merged result before insert | 422 |
| 17 | response: projection, version projection, envelope or problem, ETag, 304 | — |
| 18 | `post_*` hooks: errors logged, status unchanged | — |

An architecture test asserts the executor's call order against this table
with a recording registry, validated by swapping two steps and watching it
fail.

## 6. Driving layer

- `@<fw>/http` is transport-neutral: handlers over Web Standard
  `Request`/`Response`, a middleware contract, a route table
  (`/{schema}`, `/{schema}/_bulk`, `/{schema}/{id}`, `/{schema}/{id}/_history`,
  `/_schemas`, `/_webhooks`, `/_audit`, `/health`, `/ready`,
  `/openapi.json`), and one `buildMiddleware()` assembly point with
  numeric weights (recovery → request id → logging → security headers →
  CORS → rate limit → auth → schema version → content negotiation → ETag →
  envelope → projection → policy innermost; cache, if enabled, keyed by
  principal and inside policy).
- Framework bindings (Hono, Fastify) are thin; a **drift test** runs the
  same driving-adapter contract against both.
- Schema CRUD routes are a dynamic table looked up per request, so runtime
  schema add/update/delete and hot reload need no remount; custom routes
  mount before schema routes so they cannot be shadowed.
- `@<fw>/mcp` carries two servers (`shared/13`): the developer server the
  CLI `mcp` command starts (schema, query, codegen tools; never deployed),
  and the **application server** `createMcpServer(engine)` generated from
  the registry: `<schema>_<op>` tools whose input schemas are the registry's
  Create/Update schemas, one tool per registered Tier 3 operation with a
  `simulate_` sibling, `why_` siblings on reads, resources per entity and
  view, prompts per workflow. Each call builds a `RequestContext` with
  `channel: "mcp"`, the principal and any OBO delegation, and runs
  `OperationExecutor.run`. `tools/list` is filtered by the policy port.
  Transports: stdio and streamable HTTP via the official TypeScript SDK; the
  testing toolkit ships a client fixture and a parity suite over REST, UI
  types and tools.
- Response is the `{success, data, error, meta}` envelope with `meta.total`
  and `has_more` always present, or an RFC 7807 body, selected by config;
  both are produced by one module.

## 7. Engine and CLI

- `createEngine(cfg, options)` with pure options (`withRegistry`,
  `withEventBus`, `withMiddleware`, `withRoutes`, `withPolicy`,
  `withMigrations`, `withSchemaDir`, `withRepository`,
  `withDrivingAdapter`); nothing side-effects before `start()`.
- Start order: config → driven adapters (storage routing) → schema load
  (files, then store, store watch → registry) → ensure indexes → container
  → registry apply → subscribers → routes and middleware → listen.
  `stop()` drains and closes.
- Config is YAML plus a prefixed env override set, validated by a schema
  the framework owns.
- CLI: `init`, `run`, `schema add|list|validate`, `generate`
  (override stubs preserved on re-run), `migrate`, `mcp`, `bench`,
  `schema test`.

## 8. Files that change together

| Change | Also update |
|---|---|
| `Repository` port | every adapter, the memory adapter, `REPOSITORY_METHODS`, the contract suite |
| operator list | parser, validator, every translator, the reference evaluator, docs, OpenAPI |
| error code union | `HTTP_STATUS`, body builders, docs |
| envelope type | loader, `/_schemas` validation, codegen, docs |
| an engine option | embedding docs and the example consumer |
