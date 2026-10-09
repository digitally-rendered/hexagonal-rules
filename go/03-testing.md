# Testing (Go)

- **Table-driven tests** beside the code. `testify/require` for setup
  preconditions, `testify/assert` for assertions.
- **Unit** (`make test`): `go test ./... -short -race`. No real
  dependencies.
- **Integration** (`make test-int`): `//go:build integration` tag; Mongo via
  testcontainers, SQL via in-memory SQLite where possible. Anything touching a
  real database carries the tag.
- **HTTP-layer tests** use `sdtest.NewTestEngine(t, sdtest.WithSchemas(dir),
  sdtest.WithFunctionRegistry(reg))`: a real engine wired to
  `MemoryRepository`, so guards, validators, transforms, events and middleware
  are exercised end to end. `eng.POST("/api/v1/pets", body)` style helpers.
- **Port doubles**: `MemoryRepository` implements `port.Repository` and is
  updated with every port change; a fake that records calls is used to prove
  passthrough decorators forward every method.
- **Event assertions**: `sdtest.SubscribeAndCapture(bus, type, schema)`,
  `SubscribeAllAndCapture`, `SubscribeOnce` with cancel. Captured `Metadata`
  is a shallow snapshot at dispatch; `Input`/`Result` are by reference.
- **Codegen**: golden-file tests; regenerate with the test's `-update` flag
  when supported, otherwise update the golden deliberately.
- **Benchmarks** under `benchmarks/` for the CRUD path and query translation.
- **Coverage**: `make coverage` produces the report; CI uploads it.
- Never skip or `t.Skip` to hide a failure; a skip is allowed only for a
  missing optional integration dependency and says so.
