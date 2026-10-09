# The schema-driven hexagon (Python)

Source: [slip-stream](https://github.com/digitally-rendered/slip-stream) (library) and an application built on it.
Levels 2 and 3 of the ladder. The schema contract and versioning semantics are in
`shared/02-schema-contract.md` and `shared/03-versioned-documents.md`; this
file covers the Python structure around them.

## 1. Layer map

```
<pkg>/
├── core/                         the hexagon; never imports adapters
│   ├── domain/base.py            BaseDocument (audit fields, UUID normalisation)
│   ├── domain/models.py          hand-crafted overrides only
│   ├── domain/enums.py
│   ├── domain/schemas/*.json     Tier 1 source of truth (app)
│   ├── domain/views/*.json       Tier 2 source of truth (app)
│   ├── schema/registry.py        SchemaRegistry
│   ├── ports/                    RepositoryPort, LLMPort, ExternalDataPort, EmailPort, KeyedStorePort, …
│   ├── services/generic.py       Generic{Create,Get,List,Update,Delete,Bulk*}Service
│   ├── context.py                RequestContext, HandlerOverride
│   ├── events.py                 EventBus, HookError
│   ├── agents/ workflow/ validation/   Tier 3 domain logic (app)
├── adapters/
│   ├── api/                      EndpointFactory, schema_router, filters/, error_handler, controllers/
│   ├── persistence/db/           VersionedMongoCRUD, CRUDFactory, RepositoryFactory
│   ├── persistence/schema/       schema store (remote/persisted registry)
│   ├── streaming/ ai/ lpm/ market_data/ notifications/ esignature/ mcp/
├── container.py                  EntityContainer (composition root)
├── registry.py                   SlipStreamRegistry (decorator API)   [library]
├── app.py                        SlipStream app builder                [library]
└── main.py / config.py / dependencies.py
```

Import rules: `core` MUST NOT import `adapters`; adapters MAY import core;
adapters MUST NOT import each other; FastAPI and Motor stay in adapters (a
narrow, documented allowlist for Motor type hints in core is tolerated and
tracked to zero). `container.py` is the only module allowed to import both,
with lazy function-local imports where cycles threaten.

## 2. Library versus application

- **The library has no domain logic.** Keep it generic; anything mentioning a
  business concept belongs in a consumer. The library never modifies or reads a
  consumer project.
- **The application** owns schemas, views, Tier 3 controllers, agents, and
  adapters for its own external systems. It consumes the library's registry,
  container, factories and filters rather than re-implementing them.

## 3. The tier decision (backend)

Check before writing any endpoint (`shared/01-core-principles.md` §9):

- **Tier 1**: a schema file → 5 endpoints (POST, GET list, GET by id, PATCH,
  DELETE) with versioning, tombstone filtering and ownership scoping. Never
  hand-write these.
- **Tier 2**: a view spec → one role-scoped, filtered, sorted, paginated read.
- **Tier 3**: hand-written Python for a state machine, agent orchestration, an
  external protocol, PDF generation, or a multi-entity aggregation with real
  rules. It persists through `RepositoryPort`/`VersionedMongoCRUD`, reaches
  outward through `core/ports/`, and reuses schema-generated request/response
  models where a schema exists.

Enforced by the drift ratchet (`raw_finds_in_controllers`,
`direct_mongo_mutations`, `core_imports_adapters`, `adapter_cross_imports`).

## 4. BaseDocument

All persisted entities extend `core.domain.base.BaseDocument`: audit fields
from the schema contract, `populate_by_name`, ISO-8601 `Z` datetime
serialization, and a `model_validator(mode="before")` that normalises BSON
Binary / str / UUID by field-name convention. Do not re-implement UUID handling
in adapters.

## 5. SchemaRegistry

- Singleton; loads every `*.json` under `schema_dir` at startup; generates the
  Document/Create/Update variants; resolves collection names and owner fields;
  supports versions.
- Only the registry reads schema files. `get_collection_name` and
  `get_owner_field` are the single accessors; every factory (CRUD, repository,
  endpoint, container) calls them. A second resolution path is the defect that
  made `x-collection` silently inert for the deployed path.
- Tests reset it: `SchemaRegistry.reset()` (or `_instance = None`) in an
  autouse fixture.

## 6. EntityContainer (4-layer override)

Resolution per schema, each layer falling back independently:

| Layer | Convention | Fallback |
|---|---|---|
| 1 Models | `{models_module}.{Pascal}`, `{Pascal}Create`, `{Pascal}Update` | registry-generated |
| 2 Repository | `{repositories_module}.{name}_repository.{Pascal}Repository` | `RepositoryFactory.create()` → `VersionedMongoCRUD` |
| 3 Services | `{services_module}.{name}_service.{Pascal}{Op}Service` | `Generic{Op}Service` |
| 4 Controller | `{controllers_module}.{name}_controller.{op}_handler` or `create_router(registration)` | `EndpointFactory` |

- Discovery is by import; `_try_import` swallows only `ImportError` and
  `AttributeError`, and lets every other exception propagate so genuine bugs
  are not silenced.
- The container is initialised once in the lifespan (`init_container(names)`)
  and read via `get_container()`.
- Agent/adapter factories on the container import concrete adapters lazily
  inside the function body with a comment explaining the cycle they avoid.
- Use **decorators** for guards, validators, transforms and per-operation
  handlers; use **module overrides** when replacing the model, repository or
  service class itself. Both populate the same `handler_overrides`; decorators
  win (applied after discovery).

## 7. Generic services

`Generic{Create,Get,List,Update,Delete,BulkCreate,BulkUpdate,BulkDelete}Service[DocT, CreateT, UpdateT]`
are thin pass-throughs to `RepositoryPort`. A custom service overrides one
operation and leaves the rest generic. Services never touch the database
handle directly.

## 8. RepositoryPort

A `runtime_checkable` `Protocol` generic over Document/Create/Update:
`create`, `get_by_entity_id`, `list_latest_active`,
`list_latest_active_cursor`, `update_by_entity_id`, `count_active`,
`delete_by_entity_id`, `bulk_create`, `bulk_update`, `bulk_delete`. Any class
with those methods satisfies it (Mongo, SQL, in-memory). `isinstance(obj,
RepositoryPort)` is the contract test's assertion.

## 9. The registry decorators

```python
registry = SlipStreamRegistry()

@registry.handler("pet", "create", channel="graphql")   # replaces the service for one op (optionally one channel)
@registry.guard("pet", "delete", "update")              # pre_* first; raise HookError(403, …)
@registry.validate("order", "create", "update")         # after guards; HookError(422/409, …)
@registry.transform("user", "create", when="before")    # mutate ctx.data (before) or ctx.result (after)
@registry.on("post_create", schema_name="*")             # direct lifecycle hook
```

- Operation names and `when` are validated at decoration time (`ValueError`).
- `"*"` as schema applies to every schema.
- Nothing runs until `registry.apply(container, event_bus)` in the lifespan,
  after `init_container()` and before endpoint registration; definition order
  and module location are free.
- Execution order within `pre_*`: guards → validators → before-transforms →
  `@on` hooks. Within `post_*`: after-transforms → `@on` hooks. Global before
  schema-specific; registration order within a scope.
- A handler override that wants the default behaviour fetches the registration
  from the container and calls the default service explicitly.

## 10. RequestContext

One dataclass flows through endpoints, hooks, guards, validators, transforms
and handler overrides. Always present: `request`, `operation`, `schema_name`,
`current_user`, `db`, `extras`. Populated by the framework before hooks:
`entity_id` and hydrated `entity` (get/update/delete), `data` (create/update),
pagination and filter fields, `schema_version` (from `X-Schema-Version`),
`channel`. Populated after the service: `result`, `response`, `total_count`,
`page_info`. Bulk fields: `bulk_items`, `bulk_results`, `bulk_index`,
`atomic`.

- `RequestContext.from_request()` pulls the user from the auth filter's
  `FilterContext` when not given, and wraps plain dicts for attribute access.
- Handlers never re-fetch the entity; invalid UUID is 400 and missing entity is
  404 before any hook runs.
- `HandlerOverride` is any `async (ctx) -> Any`; it is `runtime_checkable`.

## 11. Events and HookError

- Ten core lifecycle events (`pre/post_{create,get,list,update,delete}`) plus
  bulk variants. Unknown event names raise at registration.
- `HookError(status_code, detail)` from a `pre_*` hook becomes an
  `HTTPException` and the service never runs. `HookError` from a `post_*`
  hook is a bug (500).
- `EventStreamBridge`, `AuditTrail`, `WebhookDispatcher` register on the bus;
  they are adapters and the core never imports them.

## 12. Filters (ASGI)

Onion-model middleware applied to every HTTP request (REST and GraphQL).
Order by weight: auth=10, rate-limit, content-negotiation=50, envelope=90,
projection=95, policy innermost. Filters short-circuit with structured errors.
Auth sets `request.state.filter_context`.

## 13. Errors

`structured_errors=True` yields RFC 7807 bodies (`type`, `title`, `status`,
`detail`, `instance`, plus `errors[]` on 422) with the shared status table.
Errors flow through the filter chain (negotiated, enveloped). Controllers raise
`HTTPException(404, f"{entity} not found")` only in Tier 3 code that does not
use the context pipeline.

## 14. Ownership scoping (application)

`EndpointFactory` resolves `x-owner-field` once per entity and enforces on
every generated by-id and list endpoint: privileged roles (e.g. `admin`) reach any row;
everyone else only rows whose owner field equals their id. Fail-closed
details: empty owner field → refused; caller without id → match-nothing on
list; PATCH/DELETE check before writing; 403 for "not yours", 404 for "does
not exist". The three role sets (factory, workflow controller, progress
controller) are asserted identical by a unit test. A security test asserts
the invariant over **every** aggregate with no exemption list.

## 15. Tier 3 ports

Outbound dependencies of hand-written logic are ports in `core/ports/`:
`LLMPort`, `ExternalDataPort`, `DocumentExtractionPort`, `EmailPort`,
`NotificationPort`, `KeyedStorePort`. Runtime agents receive them
through the container's `build_*_agent` factories and are tested with fakes.
A new external system = a new port + adapter + stub, never an import.

## 16. Custom endpoints

Tier 3 routers live in `adapters/api/controllers/{feature}.py` and are
registered in the main router. They take the container (not the raw db) and
call services/repositories. Request/response models come from the schema where
one exists. Routes registered in the lifespan after `include_router` do not
reach `app.routes`; register generated routers onto the API router **before**
handing it to the app (this is why the OpenAPI build for codegen constructs a
fresh app).

## 17. MCP and SDK

Two MCP servers, both adapters (`shared/13`):

- **Developer MCP** (`<fw> mcp`): schemas, queries, registry inspection and
  codegen as tools for the coding agent. Never deployed with the application.
- **Application MCP** (`generate` output, `adapters/driving/mcp/`): one tool
  per schema operation (`<schema>_<op>`) and per registered Tier 3 use case,
  a resource per entity and view, a prompt per workflow. Tool input schemas
  are the registry's Create/Update models (Pydantic → JSON Schema), never
  hand-written. Each call builds a `RequestContext(channel="mcp")` with the
  authenticated principal and any on-behalf-of delegation and runs the same
  pipeline as the router. Mutating tools have `simulate_` siblings; reading
  tools have `why_` siblings. Served over stdio and streamable HTTP with the
  official Python SDK; tested with its client fixture in CI.

Typed SDK clients are generated from the same schemas. Nothing in these
adapters reaches into persistence.
