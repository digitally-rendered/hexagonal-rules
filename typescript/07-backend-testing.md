# Backend testing (TypeScript / Node)

Source: [Syntact](https://github.com/digitally-rendered/Syntact) testing strategy (in flight) and the toolkits of the
two reference frameworks. Complements `typescript/03-testing.md`
(frontend) and `shared/07` (the vertical slice).

## 1. Absolute rules

- Never skip: `it.skip`, `describe.skip`, `test.todo`, `xit` fail CI via a
  grep check; the only allowed skip is a missing optional integration
  dependency with a reason string.
- Coverage thresholds per package (core ≥ 90%, adapters and http ≥ 85%,
  others ≥ 80%); the testing toolkit is itself tested.
- Every MUST in the backend rules names a test path; a script checks the
  paths exist.

## 2. Vitest projects (one per tier)

| Project | Runs | I/O |
|---|---|---|
| `unit:*` | per package, beside the code | none |
| `contract:*` | port contract suites over memory, in-memory Mongo, SQLite | local |
| `integration:*` | real Mongo replica set, Postgres, MySQL, Kafka, NATS, Redis via testcontainers; env-gated | containers |
| `architecture` | dependency-cruiser, restricted imports, level order, one-authority pins, lifecycle order, no-skip | none |
| `property` | fast-check properties cited by number from the design | none |
| `security` | ownership invariant over every schema, JWT negatives, rate limit, CORS, headers, policy deny, cache isolation | none |
| `e2e` | engine booted per driving adapter, lifecycle per schema, version header, hot reload | local |
| `fuzz` | OpenAPI-driven positive/negative over REST; GraphQL; MCP; stream; **zero 500s** is blocking | local |
| `bench` | see `08-performance.md` | local |

## 3. Contract suites (the standard for every port)

- `repositoryContract(makeRepo)`: create v1; update v2 with new id;
  delete tombstone; get after delete null; history; list drops tombstones
  and superseded versions; **filter after latest** (v1 status=a, v2
  status=b, v3 tombstone → filter status=a returns nothing); null clears a
  field; CAS conflict → `CONFLICT`; user unique index applies to
  latest-active only; deterministic sort with tiebreak; cursor forward and
  backward; bulk atomic versus best-effort per `capabilities`.
- `schemaStoreContract`, `auditStoreContract`, `streamerContract`,
  `policyContract`, `drivingAdapterContract(adapter)` (same routes,
  bodies and status codes across Hono and Fastify: the drift test).
- A contract suite is proven by running it against a deliberately broken
  fake and watching it fail.
- Decorator forwarding: a recording fake asserts every method in
  `REPOSITORY_METHODS` forwards.

## 4. Property tests (fast-check)

Each cites a numbered correctness property in the design: parse∘serialize
round-trips any filter; unknown field or non-scalar `_eq` always rejected;
create→get returns equal data for any generated valid payload;
`record_version` strictly increases and history length equals ops + 1;
ETag stable within and distinct across versions; specificity resolution is
a total stable order; Mongo and SQL translators agree with the reference
evaluator on any filter over a generated dataset (differential test);
deep-merge is idempotent and null removes keys; semver sort agrees with the
semver package.

## 5. Architecture tests

- dependency-cruiser as a test with an **empty** core→adapter allowlist
  and a commented adapter→adapter allowlist that fails on stale entries.
- Restricted imports: core never imports an HTTP framework, driver or
  GraphQL library; the core runtime dependency allowlist is asserted.
- Level-order test over the workspace graph.
- Lifecycle-order test against the validation table with a recording
  registry; validated by swapping two steps.
- One-authority pins: operator list, error table, audit field names, ETag,
  naming module, id minting.

## 6. The schema-driven testing toolkit

Ships as a package so consumers test their schemas the same way:

- `createTestEngine({schemas, registry, adapter, repository})` → `fetch`,
  engine, bus, repository, registry, event capture, `close`.
- `DataGenerator(seed)`: `create`, `update`, `invalid` honouring enum,
  format, min/max, pattern, required, nested; emits **only** payloads the
  validator accepts (asserted in its own test); `invalid()` emits
  type-swap, unknown-field and constraint-breaking cases.
- `LifecycleRunner`: POST 201 (never passes on 4xx) → GET → LIST contains
  → PATCH v2 with ETag change → stale `If-Match` 412 → DELETE 204 → GET
  404 → history has 3 → list excludes; bulk variant.
- `captureEvents(bus, filter)` with `waitFor(n)`.
- `hexChecks`: entity id is a UUID, record version starts at 1, audit
  timestamps present, no `deleted_at` on active documents, ETag present,
  envelope meta complete, no 500 on client error, schema version written,
  record version monotonic.
- `fuzzOpenApi(engine, {maxExamples, checks, negative})` generates from
  `/openapi.json` with the generator's invalid cases.
- `arbitraries(schema)` bridges to fast-check.

## 7. Contract and security regression

- OpenAPI baseline snapshot: no path or method removed, no new required
  field; refreshed only by a deliberate script in the same commit.
- Security suite: owner 200 / stranger 403-or-404 per posture / missing
  404 over every schema with two least-privileged principals; JWT negatives;
  rate limit; CORS; security headers; policy deny; cache never serves
  across principals.
- Supply chain: production-tree audit gate, secret scanning, a static
  analysis ruleset; dynamic API scan informational until triaged.

## 8. Fast loop, slow gates

Per-file type-check and lint while editing; one unit file per logical unit;
contract and architecture before handoff; integration, fuzz and bench once
at the checkpoint. If a slow check fails, drop back to the fast loop.
