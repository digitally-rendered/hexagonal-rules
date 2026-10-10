# Core principles (language-agnostic)

These hold in every repo on the ladder, from the hand-written DDD backend to
the Go framework. Language folders add idiom; they never relax these.

## 1. The dependency rule

1. **Core MUST NOT import adapters.** The core (domain + application, or
   `core/` in the schema-driven repos) depends only on the standard library,
   its own modules, and the port interfaces it defines.
2. **Adapters MAY import core.** They use domain models, ports, base classes.
3. **Adapters MUST NOT import sibling adapters.** An API adapter does not
   import a persistence adapter; a persistence adapter does not import an HTTP
   client adapter. Shared needs go through a port.
4. **Frameworks stay outside.** No web framework, ORM, driver, or SDK symbol
   appears in the core. Type hints count as imports.
5. **One composition root.** Exactly one place (DI container, `engine`,
   a parser's root object, `main`) knows about both ports and the adapters that
   implement them. It wires at startup. Nothing else instantiates adapters.
6. **Lazy imports in the composition root are allowed** to break cycles when
   core must reach the root for defaults; they must be function-local, with a
   comment saying why.

Enforcement: an AST-level fitness test over the real source tree, with an
**empty** allowlist for core→adapter and an explicit, commented allowlist for
adapter→adapter that fails on stale entries. Go gets this from the compiler plus
`go vet` for cycles. See `shared/04-enforcement.md`.

## 2. Ports

- A **port** is an interface in the core. It names a capability in domain
  language, never a technology (`find_by_email`, not `find_by_email_from_sql`).
- **Primary (driving) ports** are what the application exposes: use cases,
  services. **Secondary (driven) ports** are what the application needs:
  repositories, LLMs, market data, email, event publishing, caches.
- **Placement**: ports for domain concepts (repositories, domain services) live
  with the domain; ports for infrastructure concerns (email, messaging, payment)
  live with the application layer. Schema-driven repos collapse both into
  `core/ports/`.
- Ports are abstract (`ABC` + `@abstractmethod`, `Protocol`, Go `interface`).
  A port with a concrete default is a base class, not a port.
- Adding an outbound dependency means adding a port, not an import.
- Ports are focused. A port with a dozen unrelated methods is several ports.

## 3. Adapters

- **Primary adapters** (controllers, CLI, message consumers, React pages)
  translate the outside into commands/queries and call a primary port. They
  hold no business logic. They own transport concerns: status codes,
  serialization, headers, retries at the edge.
- **Secondary adapters** implement secondary ports. They translate between
  domain objects and external representations and hide every external detail.
  Technology-specific models (ORM models, API DTOs) live inside the adapter.
- Organise secondary adapters **by technology** (`sql/`, `mongodb/`, `http/`,
  `messaging/`) so shared connection handling and retry policies are reused.
- Name secondary adapters by technology (`SqlUserRepository`,
  `ShipStationAdapter`); name ports by capability (`UserRepository`,
  `ShippingPort`).
- Every adapter has an in-memory or stub sibling that satisfies the same port,
  used for integration tests of the core.

## 4. The core

- The core is a pure representation of the problem. It would be unchanged by
  swapping the database, the web framework, or the UI.
- Domain validation lives in domain objects and fails fast with domain
  exceptions that extend a base domain exception.
- Use ubiquitous language. No `Manager`, `Helper`, `Util` in the core.
- Business logic lives in entities, value objects, and domain services; use
  cases orchestrate and own cross-cutting concerns (transactions, events).

## 5. Errors

Domain errors are raised in the core with a machine-readable code and a
human-readable message, and are mapped to transport at the adapter edge. The
mapping is the same in every repo:

| Domain error | HTTP |
|---|---|
| not found (entity or schema) | 404 |
| conflict / optimistic-lock failure | 409 |
| validation failed (field details attached) / schema invalid | 422 |
| policy denied / forbidden | 403 |
| unauthenticated | 401 |
| malformed request (bad JSON, bad UUID, bad query) | 400 |
| precondition failed (`If-Match`) | 412 |
| rate limited | 429 |
| service unavailable (policy evaluator or a required dependency down) | 503 |
| internal | 500 |

This table is the only authority; language files cite it and add nothing.

- Errors carry field-level details (`field`, `message`, `code`) where relevant.
- A missing or tombstoned entity is **always** 404 before any hook runs. For
  an entity that exists but the caller does not own, `403` or `404` is one
  project-wide posture; pick it once and keep it. Check: the hydration test
  requests a missing id and a tombstoned id with a recording pre-hook
  registered, asserts 404 and asserts the hook never ran; the security suite
  asserts the one posture over every schema.
- Never let a missing column or field surface as a bare attribute error;
  model→domain conversion logs what was expected versus what was present, then
  re-raises. Check: a persistence-mapping test feeds a row missing one
  column and asserts a typed mapping error that names the expected columns.
- Structured error bodies (RFC 7807 or an equivalent `{code, message,
  details}`) are preferred and flow through the same filters as success
  responses.

## 6. The request pipeline

Every operation that enters the core runs the same ordered pipeline, whether
the framework is Python decorators, a Go registry, or a hand-written use case:

```
handler override?  → yes: handler replaces everything below for that operation
schema validation  → body against the requested version's Create/Update variant (422)
hydration          → entity for get/update/delete; missing or tombstoned is 404
guards             → authorization; first failure short-circuits
validators         → cross-field / DB-backed checks the schema cannot express
before-transforms  → normalise input (then re-validate)
pre_* hooks        → may abort
service / use case → the operation
after-transforms   → derive response fields
post_* hooks       → side effects; MUST NOT abort; failures are logged
```

This order is the authority; language files cite it and describe only how
their registry is populated. Check: every stack has a **lifecycle-order
architecture test** that runs one request through the executor with a
recording registry (one guard, one validator, one transform, one pre hook,
one post hook) and asserts the recorded order equals this list; the test is
validated by swapping two steps and watching it fail. Rungs that do not
yet pass it are recorded, dated, in `shared/05` §"Where the rungs disagree".

- A **pre** hook may abort the operation with a status code. A **post** hook
  cannot: the write is already committed, so a post-hook failure is logged
  and never changes the response (ladder resolution: the framework rungs
  win; see `shared/05`). Check: a test registers a post hook that raises,
  performs a create, and asserts the 2xx response is unchanged and the row
  is committed.
- Within **each** pipeline stage, global hooks run before schema-specific
  hooks, then most-specific scope first (§6a), then registration order. The
  order is per stage, not "all globals across every stage first".
- A single **request context** object carries the operation, schema name,
  entity id, hydrated entity, parsed input, current user, result, pagination,
  channel, and an `extras` bag between hooks. It *is* the command.
- Entity hydration for get/update/delete happens before hooks run; handlers
  never re-fetch. Missing entity is 404 before any hook.

### 6a. Scope resolution

Registrations (handlers, guards, validators, transforms, hooks, and on the
frontend track, components) are keyed by `(schema, operation, scope)` where
scope is a set of optional axes. The backend axes are **version** and
**channel**; a surface may substitute one axis (the frontend track uses
**role** in place of channel) but keeps the algorithm:

| Scope declares | Specificity |
|---|---|
| both axes match | 4 |
| second axis only (channel / role) | 3 |
| first axis only (version) | 2 |
| universal (no axis) | 1 |
| any declared axis does not match the request | excluded |

- A **handler takes one**: the single most specific match; two matches at
  the same specificity are a registration error, never a silent pick.
- **Hooks take all**: guards, validators, transforms and hooks run every
  match, most specific first, then global before schema-specific, then
  registration order.
- Resolution is a **total, stable order**: the same registry and request
  always produce the same sequence. Check: a property test asserts the
  order is total and stable over generated registries and requests, and a
  unit test asserts a non-matching axis is excluded rather than scored low.

## 7. Events

- Domain events are immutable, named in the past tense, and carry everything a
  handler needs.
- Events are raised by aggregates (classical) or by the service after the
  operation (schema-driven). Handlers are idempotent and do not mutate other
  aggregates directly.
- Lifecycle events (pre/post create, get, list, update, delete, and bulk
  variants) are the integration point for audit trails, webhooks, streaming
  bridges, and telemetry. Those consumers are adapters.

## 8. Identity

- Every persisted thing has a **stable logical identity** (`entity_id`) and,
  under versioning, a **per-version identity** (`id` / `_id`). Equality of
  entities is by logical identity only.
- Identity is minted, compared and resolved by **one function each**. Local
  re-implementation of normalisation is a known defect class. Guard it with
  a test.
- Derived identity (UUID5 from a canonical citation, content hashes) is
  deterministic; generators never invent ids. Check: a determinism test
  mints twice from the same input and asserts equality, and the fitness
  test finds the minting function called from one module only.

## 9. The tier test

Before writing code, ask which tier it belongs to:

| Tier | Backend | Frontend | What you write |
|---|---|---|---|
| 1 | entity CRUD | types and validators | nothing: a schema |
| 2 | role-scoped filtered reads | data fetching | nothing: a view spec |
| 3 | genuine domain actions | genuine UI behaviour | code, through the ports |

**The test:** delete the business logic (or the UI behaviour). If only
fetch–filter–serialize (or fetch–map–render) remains, it is Tier 1 or 2 and
must not be hand-written. Tier 3 code that uses the framework adds zero
violations; boilerplate that bypasses it fails CI. This section is the one
statement of the tier test; language files cite it.

A default screen produced by the frontend track (a design; status in
`shared/13` §2a) is Tier 1/2 output: it is generated, never hand-written. A
registered override of such a screen is Tier 3. Until the track ships,
screens are hand-written Tier 3 code over the generated types and shared
data hooks.

## 10. Contracts beat purity

Preserving an existing response shape, path, or test contract always beats
architectural tidiness. Refactor behind the contract; change the contract
deliberately and with its consumers. Check: the OpenAPI baseline snapshot
(no path or method removed, no new required field) fails on a contract
change that does not refresh the snapshot in the same commit.

## 11. One authority per vocabulary

Enumerations, stage lists, role sets, status codes, judge tables: each lives in
exactly one module, and schemas, prompts, gates, docs and tests derive from it.
Tests pin the derivation sites. Three local copies of the same policy is the
most expensive defect class observed across these repos.

## 12. Resumability

Long-running work (pipelines, vets, builds) persists progress as it lands and
is safe to kill and restart. Caches are content-addressed on everything that
affects the output and nothing that does not.
