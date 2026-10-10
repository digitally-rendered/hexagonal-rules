# Classical DDD + Ports & Adapters (Python)

Source: a classical DDD application's rule set (24 numbered rules) and its
backend patterns. This is Level 0 of the ladder: everything explicit.

## 1. Layers and imports

```
src/
├── domain/            entities, value objects, aggregates, domain services,
│   ├── model/<agg>/   domain ports (repositories), domain events
│   ├── ports/
│   ├── services/
│   └── events/
├── application/       use cases, primary ports, infrastructure ports,
│   ├── ports/primary/ commands, queries, responses, event handlers
│   ├── ports/secondary/
│   ├── use_cases/
│   ├── commands/  queries/  responses/  handlers/
├── infrastructure/
│   ├── adapters/primary/{web,cli,messaging}/
│   ├── adapters/secondary/{sql,mongodb,http,messaging,redis,crypto}/
│   └── persistence/{postgres,mongo}/      ORM models, migrations
└── configuration/     DI container, settings, wiring
```

| Layer | MUST NOT import | MAY import |
|---|---|---|
| domain | application, infrastructure, configuration, any framework (FastAPI, SQLAlchemy, Pydantic) | stdlib, typing, domain siblings |
| application | infrastructure, configuration | domain |
| infrastructure | — | domain, application |
| configuration | — | everything (only layer that knows all) |

Enforced by an AST fitness test (`tests/architecture/`) with an empty
allowlist for domain/application → infrastructure.

## 2. Entities

- `@dataclass` (not Pydantic). Identity is a typed id value object
  (`UserId`), immutable once set; auto-generated ids use `field(init=False)`
  and a `__post_init__`.
- `__eq__` / `__hash__` by identity only.
- Entities carry behaviour. An entity with only fields is anemic; put the rule
  on the entity.
- Factory method `create(...)` validates business rules and appends the
  creation event to a private `_events: list = field(default_factory=list,
  init=False)`.
- Business methods validate invariants, mutate state, append an event.
- Use domain types (`Email`, `Money`, `<Entity>Id`), not primitives, for domain
  concepts. Use domain enums, not magic strings.

## 3. Value objects

- `@dataclass(frozen=True)`. Equality on all attributes.
- Validate in `__post_init__`; raise a domain exception subclass.
- Small, focused, with meaningful methods (`Email.domain`).

## 4. Aggregates

- One aggregate root (an entity). Outside code reaches internal entities only
  through the root.
- Aggregate boundary = transaction boundary. Keep aggregates small.
- Internal collections are private; expose immutable views (`tuple(...)`).
- Complex creation goes through factory methods on the root.

## 5. Domain services

- Only when logic does not fit an entity or value object. Stateless. Operate
  on domain objects. Named in domain language. Dependencies (domain ports)
  injected through the constructor.

## 6. Repository ports

- Defined in the domain layer as `ABC` with `@abstractmethod` (they are domain
  concepts). Work with aggregate roots only. Domain-specific query methods
  (`find_active_users_in_department`), never generic CRUD leaking database
  capability. Return domain objects, never DTOs or ORM models. Raise domain
  exceptions.
- Implemented in `infrastructure/adapters/secondary/<technology>/`. Use a Unit
  of Work for transactions. Map between domain objects and persistence models
  in private `_to_domain` / `_to_model`. Optimistic concurrency via a version
  field. No business logic.

## 7. Domain events

- `@dataclass(frozen=True)`, past tense, self-contained, with `occurred_at`.
- Raised by aggregates. Published through an infrastructure port
  (`EventPublisherPort`) by the use case after the unit of work commits.
- Handlers live in the application layer (often as their own use cases), are
  idempotent, take injected dependencies, and never modify other aggregates
  directly. Cross-aggregate work is eventually consistent.

## 8. Use cases

- One class per file, one `execute(command) -> response`. Implements a primary
  port. Stateless. Orchestrates domain objects; contains no business logic.
- Owns cross-cutting concerns: unit of work, event publishing, authorization
  checks delegated to a port.
- Takes ports through the constructor: domain ports (repositories, domain
  services) and infrastructure ports (email, events, AI, rule engine).
- Returns a response DTO, never a domain object.
- **Commands** are mutable `@dataclass`; **responses** are `@dataclass(frozen=True)`.
- Validate the command, load the aggregate (404 if missing), check business
  rules (raise `BusinessRuleException`), act on the aggregate, save, log
  activity, return.

## 9. Port placement

| Port kind | Location | Examples |
|---|---|---|
| Primary | `application/ports/primary/` | `CreateUserPort`, `WorkflowExecutionPort` |
| Domain secondary | `domain/ports/` | `UserRepository`, `PricingServicePort` |
| Infrastructure secondary | `application/ports/secondary/` | `EmailNotificationPort`, `EventPublisherPort`, `AiAnalysisPort`, `RuleEnginePort`, `KeyManagementPort` |

Names end in `Port` (or `Repository` for domain repositories). Adapters carry
the technology: `SqlUserRepository`, `MongoDocumentRepository`,
`SmtpEmailAdapter`, `RestUserController`.

## 10. Primary adapters (FastAPI)

- One router per aggregate. Pydantic request/response models live in the
  controller file; they are transport DTOs, not domain objects.
- The handler: build the command, open a session via the container, resolve
  the use case, execute, map the response. Map domain exceptions to status
  codes per the shared table; let unknown exceptions surface as 500.
- No business logic, no repository access, no ORM imports in a controller.
- Use the production authentication dependency (the one that validates the
  identity provider's signed tokens); never a mock dependency in new code.
  Authorization is a port call or a role dependency, not an inline role
  string comparison. Check: a test greps the routers for the mock
  dependency's import and fails on any hit outside test fixtures.

## 11. Secondary adapters

- Organised by technology; shared base class and connection manager per
  technology.
- `_to_domain` is defensive: catch `AttributeError` separately (almost always
  a missing migration) and log the model's actual columns; catch
  `ValueError`/`TypeError` for enum/type mismatches; always re-raise.
- Retries, circuit breakers, logging and metrics are adapter concerns, applied
  with decorators at the adapter boundary. The domain never sees them.
- HTTP adapters raise a domain-meaningful error (`EmailDeliveryError`) on
  non-2xx, never leak `requests`/`httpx` exceptions.

## 12. Composition root

- `configuration/dependency_container.py` instantiates adapters, then use
  cases with adapters injected, then exposes `get_use_case(name, session)`.
- Technology choice per port is made here and only here (SQL vs Mongo
  repository for the same port).
- Configuration comes from environment/config files; factories for complex
  adapter construction; no business logic.

## 13. Persistence (SQLAlchemy + Alembic)

- Models: UUID primary keys, explicit foreign-key names
  (`ForeignKey("t.id", name="fk_…")`), timezone-aware timestamps with server
  defaults, JSONB for flexible nested data, `is_deleted` boolean soft delete.
- After every migration: `alembic check` (no drift), upgrade → downgrade →
  upgrade cycle, every model column present in the migration, every column
  read by `_to_domain` present in both. A migration missing fields blocks
  testing.

## 14. Naming

- Ubiquitous language everywhere. Intention-revealing method names. Repository
  methods reflect business queries. Value objects are named for the concept.
- `snake_case` modules, `PascalCase` classes, one use case / entity / port per
  file.

## 15. When creating new code

| New thing | Also create |
|---|---|
| domain entity | id value object, repository port, at least one adapter, in-memory adapter |
| use case | primary port, command, response, unit tests with mocked ports |
| API endpoint | controller method, use case, DTOs, API test |
| external integration | infrastructure port, adapter, stub adapter, contract test |

Never create a file without placing it in the correct layer.
