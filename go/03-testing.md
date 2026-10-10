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
- Never skip or `t.Skip` to hide a failure. The single allowed skip is the
  Class B exception of `shared/04` §5 (an environment probe for a missing
  optional integration dependency, with the reason string); the CI grep
  over `t.Skip` allows only the probe helper.

## Slice tests (the Go equivalents of `shared/07` §2)

| `shared/07` row | What proves it in Go |
|---|---|
| B1 schema | the loader test loads `schemas/<entity>.json`; the generated Document/Create/Update structs round-trip a sample payload; `schema.ValidateData` rejects an invalid one; the collision test resolves the collection through the registry accessor |
| B2 persistence | the repository contract suite run against `sdtest.MemoryRepository` and, under the `integration` tag, against Mongo via testcontainers and SQL via SQLite: create v1, update v2 new id, delete tombstone, get after delete `NotFound`, list drops tombstones and superseded versions, latest-active before filter |
| B3 ports | use-case tests with `sdtest.MemoryRepository` or a recording fake; the passthrough-forwarding test for every `port.Default*` decorator; a compile-time `var _ port.Repository = (*X)(nil)` assertion per adapter |
| B4 primary adapter | an `httptest` route-table test over `sdtest.NewTestEngine`: the five operations (or the view) are routed; owner 200, stranger 403-or-404 per the project posture, missing 404 |
| B5 composition root | `engine.New(...).Start` in a test and one request per new route through the real mux; routes registered after serving fail this test |
| C architecture | `go vet ./...` for levels; the lifecycle-order test (`go/01` §5); golden-file tests per generator (the drift check, `shared/02` §1) |
| C security | the ownership invariant iterated over every schema in the registry with two least-privileged principals |
| C contract fuzz | OpenAPI-driven fuzzing with the hex checks; zero 500s blocking |
| M agent surface | `shared/13` §5, once the application MCP server exists for this rung (design) |

Coverage: the repository's committed threshold (`make coverage`).
