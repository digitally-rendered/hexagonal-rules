# Hexagonal architecture in Go

## 1. Package map

```
pkg/core/            domain. MUST NOT import pkg/adapter/**
  errors/            DomainError, ErrorCode, HTTP mapping
  model/             Document, ListResult, ResponseEnvelope, pagination, AuditEntry
  query/             QueryDSL: FilterNode tree, operators, parser, validator
  event/             16 lifecycle event types, in-process Bus
  schema/            envelopes, definitions, registry, loader, $ref resolver, validation, migration/
  port/              Repository, Service, EventBus, WebhookDispatcher, PolicyEvaluator, AuditStore, Streamer + Default* decorators
  service/           GenericCRUDService (validate, fire events, delegate)
  registry/          FunctionRegistry: guards, validators, transforms, handlers; scope specificity
  container/         per-schema DI container
  storage/           per-schema storage routing
pkg/adapter/driving/ inbound: rest/ (Chi, GenericHandler, SchemaAPI, middleware/), graphql/
pkg/adapter/driven/  outbound: mongo/, sql/, webhook/, streaming/, policy/, telemetry/
pkg/engine/          composition root: config → driven adapters → services → driving adapters → serve
pkg/codegen/         JSON Schema → Go structs, repositories, services, handlers, overrides, OpenAPI, SDK
pkg/config/          YAML + STELLAR_* env overrides
pkg/mcp/             developer MCP server (schema, query, codegen tools; not deployed)
pkg/adapter/driving/mcp/  (design, shared/13 §2a; not in the framework today) generated application MCP server: <schema>_<op> and use-case tools, resources, prompts; RequestContext channel=mcp
pkg/testing/sdtest/  MemoryRepository, TestEngine, DataGenerator, LifecycleRunner, event capture
internal/            private utilities (stringutil, timeutil, jsonutil, ctxkey); not importable externally
cmd/                 Cobra commands: run, generate, init, schema, migrate, mcp
```

**Golden rule:** `pkg/core/**` never imports `pkg/adapter/**`. Something that
needs both puts the interface in `core/port/` and the implementation in
`adapter/driven/`.

Check: `go vet ./...` with the build-order levels of §2 fails the build when a core package imports an adapter; the import-boundary test in `go/03` asserts it.

## 2. Build-order levels (no cycles)

```
L0  internal/*, core/errors
L1  core/model, core/query, core/event
L2  core/schema, core/port
L3  core/service, core/registry, core/container, core/storage
L4  config, adapter/driven/*
L5  adapter/driving/*, codegen, mcp
L6  engine, testing/sdtest
L7  cmd
```

A package imports only lower levels. `go vet ./...` verifies.

## 3. Ports

- `port.Repository` (driven): `Create`, `FindByID`, `List`, `Update`,
  `Delete`, `BulkCreate`, `BulkUpdate`, `BulkDelete`, `EnsureIndexes`. All
  methods take `ctx` first and are schema-scoped by `schemaName`. `FindByID`,
  `Update`, `Delete` return a `NotFound` domain error. The port does not yet
  expose version history; the `<entity>_history` tool and `/_history` route
  of `shared/13` §2 apply to this rung only once a `History(ctx, schemaName,
  entityID)` method is added to the port, to every `adapter/driven/*`
  repository and to `sdtest.MemoryRepository` in the same change (§11), with
  the contract suite's history case.
- `port.Service` (driving): the same surface; validates against the schema,
  fires pre/post events, applies policy, delegates to the repository.
- Other ports: `EventBus`, `WebhookDispatcher`, `PolicyEvaluator`,
  `AuditStore` (with functional-option queries), `Streamer`.
- No `I` prefix. Interfaces live in `core/port/` or in the consumer package.
- **Passthrough decorators** `port.DefaultRepository{Inner}` and
  `port.DefaultService{Inner}` forward every method so a consumer overrides a
  subset (caching, tenant scoping, metrics, test doubles) without boilerplate.
  A nil `Inner` panics; always supply one. A test asserts every method
  forwards.

## 4. Container

- `container.New(WithDefaultRepository, WithDefaultService, WithEventBus,
  WithRepository(schema, repo), WithService(schema, svc))`; options apply in
  order.
- Resolution: schema-specific override → global default → nil (caller handles).
  A registered **handler** for a schema replaces default CRUD HTTP handling
  entirely (no service, no events, no hooks).
- Runtime registration (`RegisterRepository/Service/Handler`) for dynamically
  loaded schemas. `sync.RWMutex` inside; safe for concurrent use.
- Per-schema storage routing (`mongo` vs `sql`) is config, resolved here.

## 5. Function registry

| Kind | Signature | Effect |
|---|---|---|
| Handler | `func(w http.ResponseWriter, r *http.Request)` | bypasses the whole pipeline for that op |
| Guard | `func(ctx, r *http.Request) error` | first error denies (403) |
| Validator | `func(ctx, schemaName, data map[string]any) error` | custom cross-field or store-backed check, run **after** JSON Schema validation; error aborts (422) |
| Transform | `func(ctx, schemaName, data) (map[string]any, error)` | output replaces input; chained |

- Registered per `(schemaName, Operation, Scope{Version, Channel})`. Scope
  resolution is `shared/01` §6a with the axes **version** and **channel**;
  `FunctionRegistry` implements that scoring and nothing else: handlers take
  the single most specific match, guards/validators/transforms take every
  match most → least specific. Check: the registry's property test
  (resolution is a total stable order; a non-matching axis is excluded).
- The pipeline order is `shared/01` §6, not restated here: schema
  validation, then hydration, guards, custom validators, before-transforms,
  pre events, service, after-transforms, post events. The registry only
  supplies the guard, validator and transform stages; `GenericHandler`
  must call the service's schema validation **before** running the
  resolved validators. Check: the **lifecycle-order test** in
  `adapter/driving/rest`: a `TestEngine` with a recording `FunctionRegistry`
  (one guard, one validator, one transform, one pre and one post subscriber)
  runs one create and asserts the recorded order equals `shared/01` §6;
  validated by swapping two steps and watching it fail. Until that test
  passes, this rung is listed as dissenting in `shared/05` §"Where the rungs
  disagree" (dated).
- When a handler resolves, guards for the same op are bypassed; call
  `ResolveGuards` yourself to keep them.
- `stellar generate --overrides` scaffolds `<name>_overrides.go` with the
  four hook stubs; existing stubs are preserved on re-run.

## 6. Events

- `Event{Type, SchemaName, Timestamp, Input, Result, Metadata}`; `Metadata`
  is never nil. Pre-events carry `Input`; post-events carry both.
- 16 types: pre/post × {create, get, list, update, delete, bulk_create,
  bulk_update, bulk_delete}. `Type.IsPre()`.
- **Pre handlers may abort** (first error returned, short-circuit). **Post
  handlers cannot** (errors logged via `slog`, `Publish` returns nil).
- `Subscribe(type, schemaName, h)`; `""` = global. Global handlers run before
  schema-specific; subscription order within a scope. `SubscribeAll(schema, h)`
  for all 16.
- Webhooks, streaming bridges, telemetry and audit are subscribers; they live
  in `adapter/driven/`.

## 7. Errors

- `*errors.DomainError{Code, Message, Details, Cause}`; `Error()` formats
  `[CODE] message: cause`; `Unwrap()` returns `Cause`.
- Constructors named for the condition (`NotFound(entity, id)`,
  `Conflict(msg)`, `ValidationFailed(details...)`, `Unauthorized`,
  `Forbidden`, `BadRequest`, `Internal(msg, cause)`, `SchemaNotFound`,
  `SchemaInvalid`, `PreconditionFailed`).
- `ErrorCode.HTTPStatus()` is the single mapping and equals the shared table
  in `shared/01-core-principles.md` §5. Adapters never choose status codes
  by hand. Check: a table test asserts every `ErrorCode` maps to the row in
  the shared table.
- `Internal` wraps the cause for logs but does not expose it in the message.

## 8. Engine (composition root)

```go
eng := engine.New(cfg,
    engine.WithFunctionRegistry(funcReg),
    engine.WithEventBus(bus),
    engine.WithMiddleware(metrics, tracing),
    engine.WithPolicyEvaluator(evaluator),
    engine.WithRoutes(func(r chi.Router) { r.Post("/pets/_search", h) }),
    engine.WithSchemaDir(dir),
)
err := eng.Start(ctx) // blocks until ctx cancelled or fatal
```

- Options are pure wiring: no goroutines, no side effects until `Start`.
- Startup: load config → driven adapters → wire services → driving adapters →
  register schemas and functions → serve. Graceful shutdown drains in-flight
  requests for `cfg.Server.GracefulShutdown` then closes storage.
- Middleware: `buildMiddleware()` is the single assembly point. Recovery
  outermost; policy innermost; recovery, request-id and logging always on;
  everything else opt-in via config. Custom middleware runs **after** the
  built-in perimeter.
- Custom routes mount under the API prefix **before** schema-driven routes so
  they cannot be shadowed.
- Embed the engine in production; use the CLI for prototypes and migrations.
  `examples/petstore/` is the reference consumer; clone its `main.go`.

## 9. Schemas

- Envelope `{name, version, schema}`; version in the body, never the URL.
- Registry, loader, `$ref` resolver, validation, hot-reload watcher,
  distributed sync through the persisted schema store (change streams).
- Read-time migrations in `core/schema/migration/`; documents are always
  written at the current version.
- Query DSL parsed and validated in `core/query`, translated per adapter.
- ETag conditional requests propagate through `internal/ctxkey`, never
  globals.

## 10. Codegen

- `pkg/codegen/`: each generator is `Generate<Thing>(def, pkgName, modulePath)
  (string, error)`; `Generator.GenerateSchema` composes them. Generators:
  models (Document/Create/Update + enums), typed repository and service
  wrappers around the ports, handler with typed routes, convert helpers,
  overrides stubs, OpenAPI, GraphQL SDL, SDK.
- Golden-file tests per generator.

## 11. Files that change together

| Change | Also update |
|---|---|
| `core/port/repository.go` | every `adapter/driven/*/repository.go` and `sdtest/memory_repository.go` |
| `core/service/` surface | the service codegen template and its tests |
| envelope types | envelope docs, `schema/validation.go`, CLI envelope parsers |
| a CLI flag | the docs page for that command |
| a new `engine.Option` | embedding docs and the petstore example |
