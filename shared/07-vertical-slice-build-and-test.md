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
Never batch verification to the end. Never hand off broken work. Check: the
"what proves it" column of §2 is the gate for each phase, and the handoff
gate of §3 rejects a handoff whose summary lacks the verification output.

## 2. Layer by layer, with the test for each

Each row names **what you write** and **what proves it**, in terms every
stack has. The commands, fixtures and file names belong to the language
folders: each testing file (Python, Go, TypeScript) has a "Slice tests"
section that maps these rows to its tools. Nothing in this section names a
library.

### B1 — Schema or domain model

| Rung | What you write | What proves it |
|---|---|---|
| Schema-driven | `schemas/<entity>.json` (audit fields, `required`, `x-*` policy) and, for reads, `views/<view>.json` | the registry loads the schema; the generated Create, Update and Document variants accept a valid sample payload and reject an invalid one; the owner field resolves; the schema/collection collision check passes |
| Classical | an entity with an identity value object, value objects, a factory, business methods, events | unit tests on the factory, the invariants and the events raised; the fitness test finds no framework import |

Both: the vocabulary used by the schema or enum comes from the one authority
module, and a test pins that.

### B2 — Persistence

| Rung | What you write | What proves it |
|---|---|---|
| Versioned (schema-driven) | nothing: the generated versioned repository, plus the index plan (`(entity_id, record_version)` unique, `deleted_at`) | the **repository contract suite** (`shared/03` §1) against the in-memory double and against the real adapter: create → v1; update → v2 with a new id; delete → tombstone; get after delete → none; list drops tombstones and superseded versions; latest-active before filter |
| Relational (classical) | the table definition, a migration, a repository with defensive row→domain mapping | migration cycle up → down → up; a schema diff produces an empty migration; every column is in the migration and every mapped field is present in both; a repository integration test against a real database |

A migration that misses fields blocks all further testing.

### B3 — Ports, use cases, services

| Rung | What you write | What proves it |
|---|---|---|
| Schema-driven | nothing for Tier 1/2; for Tier 3, a port in the core and a service that takes it | use-case tests with a **stub port**; every implementation satisfies the port (the stack's conformance check); the contract suite over every adapter of the port |
| Classical | a repository port, a primary port, commands, responses, one use case per operation | use-case unit tests with a stub port: happy path, not found, business-rule failure; domain events published |

### B4 — Primary adapter

| Rung | What you write | What proves it |
|---|---|---|
| Schema-driven | nothing (the generated router) or a view spec; a Tier 3 controller only for a real action | the **route table contains the five operations** (or the view) for the schema; ownership scoping behaves: owner 200, stranger 403-or-404 per the project posture (`shared/01` §5), missing 404 |
| Classical | a controller with request and response models and the error → status mapping | API tests: validation, status codes, error mapping against `shared/01` §5; every route names its auth mechanism |

### B5 — Composition root

Register the use case in the composition root, the router in the app, the
adapter for any new port. **Routes added after the router has been mounted
never serve**; register generated routes before mounting. What proves it:
the root resolves the new use case; a request through the real app reaches
the handler (this is what catches the "never mounted" class).

### B.5 — Registration / migration validation (BLOCKING)

- Schema-driven: boot the app, read the served OpenAPI document or route
  table, confirm the five operations (or the view) appear, exercise one by
  hand or by script.
- Classical: migration cycle plus drift check, root wiring confirmed,
  controller registered.

### C — Backend test ladder

1. **Unit**: domain, models, use cases with stub ports.
2. **Integration**: repository against the test double and the real
   database; API through the app; full workflow with in-memory adapters.
3. **Architecture**: dependency boundaries, enforcement-tooling agreement,
   collision checks, drift between siblings, lifecycle order (`shared/01` §6).
4. **Security**: the ownership invariant over **every** aggregate (owner
   versus stranger of the same role); the role matrix derived from the
   installed role gates; every resource-addressing route names its
   mechanism (role gate or ownership check).
5. **Contract fuzz**: every generated endpoint with the hex checks enabled;
   new generated surfaces registered in the same change; the baseline is a
   ratchet.
6. **Ratchet**: the architecture-drift script must not increase any gated
   count.

Coverage: the repository's committed threshold. Running the unit and
integration directories alone is not "the backend passes".

### M — Agent surface (the application MCP server)

Generated from the same registry as the routes and the UI types; see
`shared/13` §5 for the steps (M1 generate, M2 register, M3 parity, M4
authorization, M5 live client, M6 agent eval). A feature without its tools
is half a feature: the agent cannot do what the human can.

### D — Frontend, bottom-up

| Step | What you write | What proves it (Phase E) |
|---|---|---|
| D1 generated types | nothing: the type generator | the drift check (`shared/02` §1) is clean; no hand-written interface duplicates a schema |
| D2 port | a port interface (classical) or none (the shared data hooks) | type-checks; a stub adapter satisfies it |
| D3 adapter | the service adapter: mapping, retry, cache, error typing | adapter tests against a mocked HTTP layer: request shape, response mapping, error transformation |
| D4 hook | an application hook calling the port, or the shared data hooks | hook tests with a stub port: state transitions, calls, errors; no client instance in a dependency array |
| D5 domain component | a pure component, props only, a test id on every interactive element | render with props, interactions, validation, and **an automated accessibility assertion in every component test file** (this is the one statement of that rule; frontend testing files cite it) |
| D6 page | composes hooks and components; layout, routing | page test with stubbed hooks or a mocked HTTP layer |
| D7 route and registration | the route in the router; the adapter registered in the services provider | the production build passes; the page is reachable |

Frontend coverage: the repository's committed threshold; build, lint and
types clean.

### F — End to end

1. Page objects for new pages.
2. Happy path per persona affected.
3. At least one **full workflow journey** per feature, run serially:
   register → approve → login → act (this is the one statement of that
   rule; frontend testing files cite it).
4. Error cases.
5. Accessibility: an automated WCAG 2.1 AA check on every new page.
6. Browsers: one engine during development; the full browser matrix before
   handoff.
7. The changed-only test map updated so selective runs still cover the
   feature.

### G — Quality gate

Hex boundaries clean (fitness tests), API paths aligned between frontend
adapters and backend routes, all suites green, every frontend builds, no
untracked TODOs, no skipped tests, coverage thresholds met, state files
updated. Then PR, and the spec is not complete until CI is green.

## 3. Rules that cut across the phases

- **Contradiction analysis first.** Compare the spec against existing
  schemas, components, other specs, and these rules before any code. Produce
  a contradiction report; resolve or escalate. Churn starts here.
- **The backend owns the contract.** An API path mismatch is fixed on the
  frontend adapter if the backend route is right, otherwise in the backend
  first, never by adding a second route. Check: Phase G's API alignment
  check (every frontend adapter path exists in the backend route table).
- **Schema registration before frontend.** The frontend consumes generated
  types from a backend that is proven to mount; never hand-write a type to
  get unblocked. Check: the frontend drift ratchet's hand-written-interface
  counter and the drift check (`shared/02` §1).
- **Fast loop during development, slow checks at handoff**: the
  verification tiers of `shared/06` §12. If a slow check fails, drop back to
  the fast loop to fix. Scope every command to the file or test in play and
  use quiet reporters; summarise results instead of pasting output.
- **Every handoff carries evidence**: files created/modified, wiring changes,
  the API contract (backend → frontend), assumptions, known issues, and the
  verification output. Missing summary or missing state-file update rejects
  the handoff.
- **Checkpoints name commands and pass criteria.** "All tests pass" is not a
  checkpoint; "the unit suite command exits 0 with fail-fast on, and coverage
  on new files meets the committed threshold" is.
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

### G.1 — Look at it

Before the quality gate, capture every new or changed screen and state in a
real browser at desktop and phone width and in each colour mode, and have a
person review the captures. Axe and structure tests prove the markup; they do
not notice a default-styled button, a raw validator message, a missing
default value or a developer error page. Check: the capture script exists and
its output is attached to the handoff; each defect found becomes a
remediation row (`specs/05` §2) before the slice is called done.

## 5. The definition of done

All tasks checked; migration or registration validated; defensive conversion
everywhere; backend unit + integration green with coverage; application MCP
generated with parity, live-client and agent-eval tests green; frontend unit
green with coverage; the accessibility assertion in every component test
(§2 D5); builds clean; E2E across the browser matrix with the full workflow
journey (§2 F) and the page accessibility check; no hex violations;
API aligned; lint and types clean on both sides; CI green; progress and
known-issues files updated.
