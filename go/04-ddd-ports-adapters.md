# Classical DDD + Ports & Adapters (Go)

The Level 0 rung in Go. Same rules as `python/01-ddd-ports-adapters.md`;
this file is the Go idiom. Stack assumed: Go ≥ 1.22, Chi, `database/sql`
with `sqlc` or `pgx`, `golang-migrate` or `goose`, the official Mongo driver,
`log/slog`, testify, testcontainers-go.

## 1. Packages and imports

```
internal/
├── domain/            entities, value objects, aggregates, domain services, repository interfaces, events
│   ├── <agg>/
│   ├── shared/        ids, money, email, enums
│   └── event/
├── app/               use cases, commands, responses, infrastructure ports
│   ├── port/          secondary ports (email, events, ai, keys)
│   └── usecase/<agg>/
├── adapter/
│   ├── driving/{http,cli,messaging}/
│   └── driven/{sql,mongo,http,messaging,redis,crypto}/
└── wire/              composition root
cmd/<service>/main.go
```

| Package | MUST NOT import | MAY import |
|---|---|---|
| `domain/**` | `app`, `adapter`, `wire`, any driver or framework | stdlib, domain siblings |
| `app/**` | `adapter`, `wire` | `domain` |
| `adapter/**` | — | `domain`, `app` |
| `wire`, `cmd` | — | everything |

The compiler forbids cycles; `depguard` (golangci-lint) or a build-level
test (`go list -deps` assertion) forbids the downward imports listed.
`internal/` keeps the whole tree private to the module.

## 2. Entities, value objects, aggregates

- Typed ids: `type UserID struct{ v uuid.UUID }` with `NewUserID()`,
  `ParseUserID(string)`, `String()`. Never bare strings or `uuid.UUID`.
- Entities are structs with unexported fields and methods that enforce
  invariants and append to an unexported `events []event.Event`;
  `PullEvents()` drains it. Equality by id only.
- Value objects are small structs with unexported fields, constructed only
  through `NewEmail(string) (Email, error)`; comparable with `==` when all
  fields are comparable. No pointers to value objects.
- Factories `NewOrder(...) (*Order, error)` validate business rules and
  record the creation event.
- Domain errors are sentinel values or small types in `domain/shared`
  (`ErrNotFound`, `ErrConflict`, `ValidationError{Field, Reason}`), wrapped
  with `%w`, checked with `errors.Is/As`.
- Domain services are structs taking domain repository interfaces.

## 3. Ports

- Repository interfaces live in the domain package that owns the aggregate
  (`domain/user/repository.go: type Repository interface`), methods take
  `ctx` first, return domain types and domain errors.
- Infrastructure ports live in `app/port` (`EmailSender`, `EventPublisher`,
  `KeyManager`, `Assistant`). Interfaces are small; split rather than grow.
- `DefaultXxx` passthrough structs make partial fakes cheap.
- Every port has an in-memory implementation in `<pkg>/mem` for tests.

## 4. Use cases

- One struct per use case with an `Execute(ctx, Command) (Response, error)`
  method; dependencies are interfaces in the constructor
  (`NewCreateUser(repo, uow, events)`), options via functional options when
  configurable.
- Commands and responses are plain structs; responses copy out values
  (never return domain pointers).
- A `UnitOfWork` interface `Do(ctx, func(ctx) error) error` wraps the
  transaction; the SQL adapter binds the tx into `ctx`.

## 5. Driving adapters (HTTP)

- One handler struct per aggregate with `Routes() chi.Router`.
  Request/response structs with JSON tags live in the handler file;
  validation is explicit (or via `validator`); they are transport DTOs.
- The handler decodes, builds the command, calls the use case, encodes the
  response; `errors.As` against the domain error set selects the status via
  one `httpStatus(err)` function per the shared table. Unknown errors →
  500 with a problem-details body and a logged cause.
- Middleware chain: recovery → request id → logging → security headers →
  CORS → rate limit → auth → policy; custom middleware after the perimeter.

## 6. Driven adapters

- Per technology package with a shared client and retry policy.
- `toDomain(row)` returns `(T, error)`; a missing or malformed column
  produces a `MappingError{Table, Column, Cause}` and is logged with the
  expected columns; never a panic, never a silent zero value.
- HTTP adapters translate non-2xx into domain-meaningful errors; driver
  errors never cross the port.
- Cross-cutting concerns (retry, circuit breaker, metrics) are decorator
  structs embedding the inner port.

## 7. Composition root

- `wire/` (hand-written or `google/wire`) builds driven adapters, then use
  cases, then driving adapters, chooses the technology per port, and returns
  an `App` with `Start(ctx)`/`Stop(ctx)`. `cmd/<service>/main.go` only loads
  config, builds, handles signals.
- Config is a struct loaded once (env + file) and validated; nothing reads
  `os.Getenv` elsewhere.

## 8. Persistence (SQL)

- Schema in migration files; `sqlc` generates typed queries; table models
  stay in the adapter package. UUID keys, explicit FK names, `timestamptz`
  with defaults, JSONB for nested data, `is_deleted` soft delete.
- After every migration: up → down → up and a drift check against the
  schema snapshot in CI.

## 9. Naming

Files `snake_case.go`; exported `PascalCase`; acronyms `ID`, `URL`, `HTTP`.
Interfaces named for the capability (`user.Repository`, `port.EmailSender`);
implementations carry the technology (`sqluser.Repository`,
`sendgrid.Sender`, `httpapi.UserHandler`). One use case per file.
