# Classical DDD + Ports & Adapters (TypeScript / Node)

The Level 0 rung for a TypeScript backend. Same rules as
`python/01-ddd-ports-adapters.md`; this file is the TypeScript idiom.
Stack assumed: Node ≥ 20, TypeScript strict, ESM, Fastify (or Hono),
Zod for transport validation, Kysely/Drizzle or Prisma for SQL, the official
Mongo driver, Pino, Vitest.

## 1. Layers and imports

```
src/
├── domain/            entities, value objects, aggregates, domain services, domain ports, events
│   ├── model/<agg>/
│   ├── ports/
│   ├── services/
│   └── events/
├── application/       use cases, primary ports, infrastructure ports, commands, queries, responses, handlers
│   ├── ports/primary/  ports/secondary/
│   ├── use-cases/  commands/  queries/  responses/  handlers/
├── infrastructure/
│   ├── adapters/primary/{http,cli,messaging}/
│   ├── adapters/secondary/{sql,mongodb,http,messaging,redis,crypto}/
│   └── persistence/{postgres,mongo}/      tables/schemas, migrations
└── configuration/     composition root, settings
```

| Layer | MUST NOT import | MAY import |
|---|---|---|
| domain | application, infrastructure, configuration, any framework or driver, Zod | node built-ins, domain siblings |
| application | infrastructure, configuration | domain |
| infrastructure | — | domain, application |
| configuration | — | everything |

Enforced by `eslint-plugin-boundaries` (or `no-restricted-imports` per
layer) at authoring time and by `dependency-cruiser` in CI with an empty
allowlist for domain/application → infrastructure. Path aliases
`@domain/*`, `@application/*`, `@infrastructure/*` make violations greppable.

## 2. Entities, value objects, aggregates

- Entities are plain classes with a `readonly id: UserId` branded type;
  equality by id (`equals(other)`), never structural.
- Value objects are immutable: `readonly` fields, `Object.freeze` in the
  constructor, validation in a private constructor plus a static `create()`
  that returns the object or throws a domain error. Equality is structural
  (`equals`). No Zod in the domain; Zod belongs at the transport edge.
- Branded ids: `type UserId = string & { readonly __brand: 'UserId' }` with
  `UserId.generate()` / `UserId.from()` factories. Never pass raw strings.
- Aggregates expose a private `_events: DomainEvent[]` with
  `pullEvents()`; internal collections are returned as `ReadonlyArray`.
- Domain services are stateless classes taking domain ports in the
  constructor.
- Domain errors extend one `DomainError` base with a `code` discriminant;
  `instanceof` and `code` both work across bundles.

## 3. Ports

- Ports are `interface`s (or `abstract class` when a default is needed) in
  `domain/ports` (repositories, domain services) and
  `application/ports/secondary` (email, events, AI, key management).
  Primary ports are interfaces in `application/ports/primary`.
- Repository ports work with aggregate roots, use domain query names, return
  domain objects, and reject with domain errors. Async everywhere
  (`Promise<User | null>`).
- An in-memory implementation ships beside every port for tests.

## 4. Use cases

- One class per file, one `execute(command): Promise<Response>`, implements a
  primary port. Commands are plain mutable objects; responses are
  `Readonly<...>` and built with `Object.freeze`.
- Orchestrate: validate → load (not found → domain error) → business rules
  → act → save inside a unit of work → publish events → return a DTO.
- A `UnitOfWork` port wraps a transaction (`withTransaction(fn)`); the SQL
  adapter maps it to the driver's transaction.

## 5. Primary adapters (HTTP)

- One router plugin per aggregate. Request and response schemas are Zod
  objects in the controller file and generate the OpenAPI document
  (`zod-to-openapi` or Fastify's type provider). They are transport DTOs,
  never domain objects.
- The handler: parse (Zod) → build the command → resolve the use case from
  the container → execute → map the response. Map domain errors to status
  with one `errorToHttp(code)` table per the shared table; unknown errors
  surface as 500 with a problem-details body.
- Authentication is a plugin that sets a typed `request.principal`;
  authorization is a port call, never inline role string comparison.

## 6. Secondary adapters

- By technology. A shared base per technology (client, retry policy,
  logging) and one adapter per port.
- `toDomain(row)` is defensive: a missing column throws a typed
  `PersistenceMappingError` naming the table's expected columns; enum
  mismatches throw with the offending value; always rethrow after logging.
- HTTP adapters raise domain-meaningful errors; driver exceptions never
  cross the port.
- Retries, circuit breakers and metrics are decorators around the adapter
  (`withRetry(adapter)`), not inside use cases.

## 7. Composition root

- `configuration/container.ts` builds adapters, then use cases, then
  routers; exposes `getUseCase(name)`. Choose technology per port here only.
  No DI framework is required; a plain factory module with memoisation is
  enough. Lazy `await import()` is allowed here to break cycles, commented.
- Settings come from `process.env` validated once by a Zod schema at
  startup; nothing reads `process.env` elsewhere.

## 8. Persistence (SQL)

- Tables typed (Kysely `Generated<>`/Drizzle schema) with UUID primary keys,
  explicit FK names, timezone-aware timestamps with defaults, JSONB for
  nested data, `is_deleted` soft delete.
- Migrations are versioned files; after each: up → down → up, a drift check
  (generate a migration from the schema and require it empty), every
  `toDomain` field present in the table type and the migration.

## 9. Naming

- `kebab-case` files, `PascalCase` classes and types, `camelCase` members,
  `UPPER_SNAKE_CASE` constants. One use case / entity / port per file.
  Ports are `UserRepository`, `EmailNotificationPort`; adapters carry the
  technology: `SqlUserRepository`, `SendGridEmailAdapter`,
  `FastifyUserController`.
