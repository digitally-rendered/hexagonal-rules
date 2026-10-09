# Conventions (Go)

- **Interfaces**: accept interfaces, return structs. No `I` prefix. Define in
  the consumer package or `core/port/`.
- **Errors**: wrap with `fmt.Errorf("operation: %w", err)`. Sentinel errors in
  `core/errors/`; structured errors as types. **Every error return is
  checked** (`errcheck` in CI). Deferred closes: `defer func() { _ =
  x.Close() }()`. CLI output: `_, _ = fmt.Fprintf(...)`.
- **Context**: first parameter of every public function; propagate, never
  store in structs.
- **Options**: functional options (`type Option func(*Config)`) for
  configurable constructors; options are pure wiring.
- **Naming**: files `snake_case.go`; exports `PascalCase`; acronyms all caps
  (`ID`, `URL`, `HTTP`). Constructors named for the condition they describe
  when returning rich types (`NotFound`, not `ErrNotFound`).
- **Packages**: one responsibility each. No `utils`/`helpers`; use specific
  names (`stringutil`, `timeutil`). `internal/` for anything not part of the
  public library surface.
- **Middleware**: `func(http.Handler) http.Handler`, Chi/stdlib compatible.
- **Concurrency**: `sync.RWMutex` for shared state; channels for coordination.
  Tests run with `-race`.
- **Formatting**: `gofmt -w .` before every commit; no exceptions.
- **Lint** (golangci-lint v2, enforced): `errcheck`, `govet`, `staticcheck`,
  `unused`, `ineffassign`, `gofmt`. No unused functions, variables, fields or
  imports. Follow staticcheck suggestions (e.g. `fmt.Fprintf` over
  `WriteString(Sprintf(...))`). Run `make lint` before pushing.
- **Logging**: `log/slog`; post-event handler failures are logged, not
  returned.
- **Config**: YAML with `STELLAR_`-prefixed env overrides; no hardcoded
  connection strings.
- **CLI**: one Cobra command per file in `cmd/`, registered in `init()`.
- **Commands**: `make build|test|test-int|lint|vet|generate|coverage|tidy`. CI
  on every PR: lint → `go vet` + `go test ./... -short -count=1 -race` →
  coverage → build.
