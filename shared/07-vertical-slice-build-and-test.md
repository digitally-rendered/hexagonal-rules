# Building from the schema up to the UI, and testing every layer on the way

Source: the feature lifecycles, new-entity workflows and verification
methodology of the application sources; [slip-stream](https://github.com/digitally-rendered/slip-stream) testing
utilities; pipeline gates. One feature is one **vertical slice** through the
hexagon. The slice is built bottom-up (schema → persistence → core → API →
generated contract → agent surface → frontend → E2E), and each layer carries its own test
that must pass before the next layer is built.

## 1. The order

```
Phase A    Prepare: read spec, state files, dependencies; inventory what exists
Phase A.5  Contradiction analysis — BLOCKING: spec vs code, spec vs spec, spec vs rules
Phase B    Backend, bottom-up
             B1 schema / domain model
             B2 persistence (migration or collection + indexes)
             B3 ports + use cases / services
             B4 primary adapter (controller or generated router)
             B5 composition root wiring
Phase B.5  Registration / migration validation — BLOCKING
Phase C    Backend tests (unit → integration → contract → security → fuzz)
Phase M    Agent surface: generated MCP tools, resources, prompts → parity → authorization → live client → agent eval
Phase D    Frontend, bottom-up: generated types → port → adapter → hook → domain component → page → route
Phase E    Frontend tests (component + a11y → hook → adapter)
Phase F    E2E (page objects → happy path → full workflow → errors → a11y → browsers)
Phase G    Quality gate (hex boundaries, API alignment, all suites, builds, no TODOs)
Phase G.5  Push, PR, CI green — BLOCKING
Phase H    Completion: tasks, sequencing, state files, handoff summary
```

Each phase ends with a verification that must pass before the next begins.
Never batch verification to the end. Never hand off broken work.

## 2. Layer by layer, with the test for each

### B1 — Schema or domain model

| Rung | What you write | Test before moving on |
|---|---|---|
| Schema-driven | `schemas/<entity>.json` (audit fields, `required`, `x-*` policy) and, for reads, `views/<view>.json` | schema loads in the registry; generated Create/Update/Document models validate sample payloads; `x-owner-field` resolves; schema/collection collision test passes |
| Classical | entity dataclass with id value object, value objects, factory, business methods, events | unit tests on factory, invariants, events raised; no framework imports (fitness test) |

Both: the vocabulary used by the schema or enum comes from the one authority
module, and a test pins that.

### B2 — Persistence

| Rung | What you write | Test |
|---|---|---|
| Mongo versioned | nothing (generated `VersionedMongoCRUD`) plus index plan: `(entity_id, record_version)` unique, `deleted_at` | versioned CRUD tests against mongomock: create → v1; update → v2, new id; delete → tombstone; get after delete → None; list drops tombstones and superseded versions |
| SQL classical | SQLAlchemy model, Alembic migration, SQL repository with defensive `_to_domain` | migration cycle upgrade → downgrade → upgrade; autogenerate produces an empty migration; every model column in the migration; every `_to_domain` field in both; repository integration test against a real DB |

A migration that misses fields blocks all further testing.

### B3 — Ports, use cases, services

| Rung | What you write | Test |
|---|---|---|
| Schema-driven | nothing for Tier 1/2; for Tier 3, a port in `core/ports/` and a service/agent that takes it | use case tests with the port mocked or stubbed; `isinstance(impl, Port)` for every implementation; contract test over every adapter of the port |
| Classical | repository port (ABC), primary port, commands, responses, one use case per operation | use-case unit tests with `AsyncMock(spec=Port)`: happy path, not-found, business-rule failure; domain events published |

### B4 — Primary adapter

| Rung | What you write | Test |
|---|---|---|
| Schema-driven | nothing (EndpointFactory) or a view spec; Tier 3 controller only for real actions | generated router registers; endpoint appears in `/docs` with all five operations; ownership scoping behaves (owner 200, stranger 403, missing 404) |
| Classical | FastAPI controller with request/response models, exception → status mapping | API tests: validation, status codes, error mapping; every route has an auth mechanism |

### B5 — Composition root

Register the use case in the container, the router in the app, the adapter
for any new port. **Routes added after the router has been included never
mount**; register generated routers before handing the router to the app.
Test: the DI container resolves the new use case; a request through the real
app reaches the handler (this is what catches the "never mounted" class).

### B.5 — Registration / migration validation (BLOCKING)

- Schema-driven: start the server, open `/docs`, confirm the five CRUD
  operations (or the view) appear, exercise one by hand or by script.
- Classical: migration cycle plus drift check, container wiring confirmed,
  controller registered.

### C — Backend test ladder

1. **Unit** (`tests/unit/`): domain, models, use cases with mocked ports.
2. **Integration** (`tests/integration/`): repository against mock/real DB;
   API through the app; full workflow with in-memory adapters.
3. **Architecture** (`tests/architecture/`): AST boundaries, enforcement
   tooling agreement, collision checks, drift between siblings.
4. **Security** (`tests/security/`): ownership invariant over **every**
   aggregate (owner vs stranger of the same role); role matrix derived from
   installed `require_role` calls; every resource-addressing route names its
   mechanism (role gate or ownership check).
5. **Contract fuzz** (`tests/schemathesis/`): every generated endpoint with
   the hex checks enabled; new generated surfaces registered here in the same
   change; baseline is a ratchet.
6. **Ratchet**: the architecture-drift script must not increase any gated count.

Coverage: 80% (schema-driven app) or 100% on new code (classical). `pytest
tests/unit tests/integration` is not "the backend passes".

### M — Agent surface (the application MCP server)

Generated from the same registry as the routes and the UI types; see
`shared/13` §5 for the steps (M1 generate, M2 register, M3 parity, M4
authorization, M5 live client, M6 agent eval). A feature without its tools
is half a feature: the agent cannot do what the human can.

### D — Frontend, bottom-up

| Step | What you write | Test (Phase E) |
|---|---|---|
| D1 generated types | nothing: the type generator → `types.ts`, `schemas.ts`, `views.ts`, `apiTypes.ts` | `codegen:check` clean; no hand-written interface duplicates a schema |
| D2 port | `ports/I<Capability>Service.ts` (classical) or none (generated hooks) | type-checks; stub adapter satisfies it |
| D3 adapter | `adapters/secondary/<Capability>ServiceAdapter.ts`: mapping, retry, cache, error typing | adapter tests with MSW: request shape, response mapping, error transformation |
| D4 hook | `application/hooks/use<Capability>.ts` calling the port, or `useEntity`/`useEntityList`/`useView` | hook tests with a stub port: state transitions, calls, errors; no `apiClient` in dependency arrays |
| D5 domain component | pure component, props only, `data-testid` on interactive elements | render with props, interactions, validation, and an `axe` assertion in every component test file |
| D6 page | composes hooks + components; layout, routing | page test with stubbed hooks or MSW |
| D7 route + service registration | route in the router; adapter registered in the services provider/factory | `npm run build` passes; the page is reachable |

Frontend coverage: 70% overall or 100% on new code; build, lint, types clean.

### F — End to end

1. Page objects for new pages.
2. Happy path per persona affected.
3. At least one **full workflow** (`test.describe.serial`) per feature:
   register → approve → login → act.
4. Error cases.
5. Accessibility: axe-core WCAG 2.1 AA on every new page.
6. Browsers: chromium during development; desktop cross-browser before
   handoff; mobile in the deploy gate.
7. `test-map.json` updated so changed-only runs still cover the feature.

### G — Quality gate

Hex boundaries clean (AST tests), API paths aligned between frontend adapters
and backend routes, all suites green, both frontends build, no untracked
TODOs, no skipped tests, coverage thresholds met, state files updated. Then
PR, and the spec is not complete until CI is green.

## 3. Rules that cut across the phases

- **Contradiction analysis first.** Compare the spec against existing
  schemas, components, other specs, and these rules before any code. Produce
  a contradiction report; resolve or escalate. Churn starts here.
- **The backend owns the contract.** An API path mismatch is fixed on the
  frontend adapter if the backend route is right, otherwise in the backend
  first, never by adding a second route.
- **Schema registration before frontend.** The frontend consumes generated
  types from a backend that is proven to mount; never hand-write a type to
  get unblocked.
- **Fast loop during development, slow checks at handoff.** Lint and types
  per file; one unit test file per logical unit; integration, coverage,
  cross-browser and E2E once at handoff. If a slow check fails, drop back to
  the fast loop to fix. Scope every command to the file or test in play and
  use quiet reporters; summarise results instead of pasting output.
- **Every handoff carries evidence**: files created/modified, wiring changes,
  the API contract (backend → frontend), assumptions, known issues, and the
  verification output. Missing summary or missing state-file update rejects
  the handoff.
- **Checkpoints name commands and pass criteria.** "All tests pass" is not a
  checkpoint; "`pytest tests/unit -x -q` exits 0 and coverage on new files is
  100%" is.
- **Periodic quality pass** after every two or three features: consolidate
  duplicates, align patterns, remove dead code, update docs.
- **Code-graph gates** (`shared/12`): index fresh at session start and
  after any branch change; `impact` before editing an existing symbol and
  `api_impact` before changing a route handler; `detect_changes` in the
  quality gate before commit; cross-repo `group_contracts` for the API
  alignment check when backend and frontend are separate repos.

## 4. Blocking conditions

Stop and fix before continuing when: backend tests fail (no frontend work);
a hex boundary is violated (fix immediately); an API path mismatches; DI
wiring is missing; migration validation fails; a `_to_domain` attribute error
appears (missing migration or column); a build fails; a handoff lacks
verification, summary, or state-file updates; a file-ownership violation
occurs.

## 5. The definition of done

All tasks checked; migration or registration validated; defensive conversion
everywhere; backend unit + integration green with coverage; application MCP
generated with parity, live-client and agent-eval tests green; frontend unit
green with coverage; axe in every component test; builds clean; E2E in every
browser project with a full-workflow test and a11y check; no hex violations;
API aligned; lint and types clean on both sides; CI green; progress and
known-issues files updated.
