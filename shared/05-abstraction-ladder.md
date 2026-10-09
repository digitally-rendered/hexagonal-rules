# The abstraction ladder

The sources are not five architectures. They are one hexagon at five levels
of abstraction. Each level keeps every invariant of the one below it and
replaces hand-written structure with generated or framework-provided
structure. Pick the lowest level that expresses your domain, and move up when
the hand-written boilerplate outweighs the custom logic.

## The rungs

### Level 0 — Classical DDD + Ports & Adapters (a hand-written application)

Everything is explicit code. One entity means: a dataclass entity with
behaviour and an `_events` list, value objects, a repository port (ABC) in
`domain/ports/`, a SQL/Mongo adapter in `infrastructure/adapters/secondary/`,
a use case implementing a primary port in `application/`, mutable command and
frozen response DTOs, a thin FastAPI controller, and a DI container entry.
Right when the domain is rich (many aggregates with behavioural invariants
and cross-cutting rules) and the invariants live in behaviour, not in field
shapes.

Rules: `python/01-ddd-ports-adapters.md`.

### Level 1 — Hexagon + plugin ensemble + pipeline (a pipeline application)

Still hand-written core, but the variable part of the system (how to extract a
field, how to detect an entity, how to judge an artifact) is a **plugin**
behind a base contract, discovered by a repository port, run by a service in
priority order, and recorded with provenance. Long-running work is a pipeline
of typed stages with a content-addressed cache. Quality is measured by an
independent judge layer and deterministic gates rather than by the
generator's own confidence.

Rules: `python/03-plugin-pipeline.md`, `shared/06-evals-and-verification.md`.

### Level 2 — Schema-driven application

JSON Schema becomes the domain definition for Tier 1 entities. The registry
generates models, versioned CRUD, endpoints, frontend types, validators and
mappers. View specs generate Tier 2 role-scoped reads. Hand-written code is
reserved for Tier 3 domain actions, which still go through ports
(`LLMPort`, `ExternalDataPort`, `RepositoryPort`). A 4-layer container lets a
module override any layer per entity by naming convention. An enforcement
ratchet makes bypassing the framework a CI failure.

Rules: `python/02-schema-driven-framework.md`, `typescript/02-generated-layer.md`.

### Level 3 — The framework as a library ([slip-stream](https://github.com/digitally-rendered/slip-stream))

Level 2 with the domain removed. The library has **no domain logic** and must
stay generic. Customisation is declarative: registry decorators (`@handler`,
`@guard`, `@validate`, `@transform`, `@on`), channel scoping, module-convention
overrides, an ASGI filter chain, a request context that is the command, event
streaming bridges, audit trail, webhooks, policy evaluation, SDK generation,
an MCP server, and reusable schemathesis checks for the hex invariants.

Rules: `python/02-schema-driven-framework.md` (library sections).

### Level 3.5 — Typed library with package-level boundaries ([Syntact](https://github.com/digitally-rendered/Syntact), TypeScript)

Level 3 in a language where the workspace package graph is the layer graph:
one package per hex level, a transport-neutral driving layer with thin
framework bindings and a drift test between them, one executor for every
channel, optimistic concurrency by construction, and a shipped
schema-driven testing toolkit. In flight.

Rules: `typescript/06`–`08`.

### Level 4 — Compiled framework ([stellar-drive](https://github.com/digitally-rendered/stellar-drive), Go)

The same model where the compiler enforces the dependency rule, package build
levels make cycles impossible, interfaces are the ports, passthrough decorator
structs make partial overrides cheap, a function registry resolves overrides
by **scope specificity** (version + channel), an engine is the single
composition root, and codegen emits typed wrappers, OpenAPI and SDKs from
schemas.

Rules: `go/`.

## What is invariant on every rung

- The dependency rule and the single composition root.
- Ports as abstractions in the core; adapters by technology outside it.
- The pipeline order (override → guards → validators → transforms → service →
  post hooks) and pre/post abort semantics.
- Domain errors with codes mapped to transport at the edge.
- Stable logical identity separate from version identity.
- Never skip a test; a rule names its check; overrides have a reason at the
  site.

## What each rung adds

| Rung | Adds | Removes from your hands |
|---|---|---|
| 0 | explicit entities, value objects, aggregates, use cases | nothing |
| 1 | plugin contract, provenance, stage cache, judge layer, gates | per-extractor orchestration, resumability bookkeeping |
| 2 | schema registry, generated CRUD/endpoints/types, tiers, ownership scoping, ratchet | Tier 1/2 code entirely |
| 3 | decorators, request context, filters, events, override modules, test utilities | app-specific framework code |
| 4 | compile-time boundaries, scope specificity, engine options, codegen | runtime import discipline |

## Choosing a rung

- Rich behavioural invariants, few entities, relational data with migrations →
  **Level 0**.
- Many interchangeable strategies competing on the same input, long batch
  work, generated artifacts that need vetting → **Level 1** (often on top of 0
  or 2).
- Dozens of CRUD-shaped entities with audit requirements and a thin layer of
  real actions → **Level 2**, built on **Level 3** rather than re-implementing
  it.
- Multiple services needing the same framework, or a performance/ops
  requirement for a single static binary → **Level 4**.

A product usually mixes rungs: Level 2 for its catalogue entities, Level 0
for its one rich aggregate, Level 1 for its ingestion pipeline. The import
rules are identical across the mix.

## Moving up

1. Identify Tier 1 entities (delete the logic; only CRUD remains). Move them to
   schemas. Keep the old controller behind the generated one until the contract
   is proven identical, then delete it.
2. Identify Tier 2 reads. Move them to view specs.
3. What remains is Tier 3. Route its persistence through the repository port
   and its external calls through ports. Count violations; baseline; ratchet.
4. Extract anything with no domain knowledge into the library rung.

## Where the rungs disagree

| Topic | Level 0 says | Levels 2–4 say | Resolution |
|---|---|---|---|
| Where the domain model lives | code (dataclasses) | the schema file | schema for Tier 1; code for aggregates with behaviour |
| Repository port placement | `domain/ports/` for repos, `application/ports/secondary/` for infra | `core/ports/` for all | either; one convention per repo |
| Persistence of deletes | `is_deleted` flag, in-place update | tombstone version | tombstone when an audit trail is required |
| Case conversion at the API edge | axios-case-converter middleware | generated per-schema mappers, no middleware | generated mappers when a codegen exists; middleware otherwise |
| Line length | 100 | 88 | per repo; never mixed |
| Hook order across stages | — | some rungs ran all global hooks before any schema-specific hook | global-before-specific **within each stage** (`shared/01` §6) |
| Post-hook failure | — | one rung surfaced it as 500 | logged, response unchanged: the write is committed (`shared/01` §6) |
| Custom validators vs schema validation | — | one rung ran custom validators before schema validation | schema validation first, then guards, then custom validators |
| ETag source | — | header, body hash, and id:version schemes coexisted | one function over the result object (`entity_id:record_version`) |
| Operator spelling | — | `_startswith` vs `_starts_with` | `_startswith` canonical; the alias accepted and normalised at parse |
| UUID storage in Mongo | BSON Binary | strings (v7) | one per project; normalisation rule in `shared/03` §6 |
