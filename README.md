# hexagonal-rules

Consolidated hexagonal-architecture and domain-driven-design rules, distilled
from five production codebases and organised **per language**. This folder is
the single place the rules live; the source repositories are read-only inputs
and are never edited from here.

## Lineage

The rules were distilled from two public frameworks and several private
applications built on the same architecture.

| Source | Language | What it contributed |
|---|---|---|
| [slip-stream](https://github.com/digitally-rendered/slip-stream) | Python | The schema-driven hexagon as a generic library: registry decorators, `RequestContext`, filters, events, 4-layer container, testing utilities |
| [stellar-drive](https://github.com/digitally-rendered/stellar-drive) | Go | The same model ported to Go with compile-time enforcement: package levels, function registry with scope specificity, event bus, domain errors, engine composition root |
| [Syntact](https://github.com/digitally-rendered/Syntact) | TypeScript | The same model in TypeScript (in flight): monorepo package levels as rung-1 enforcement, transport-neutral driving layer, one executor for every channel, CAS-based versioning, the schema-driven testing toolkit, benchmark ratchet |
| a classical DDD application | Python + React/TS | Explicit DDD + Ports & Adapters (entities, value objects, aggregates, use cases, ports), React hexagonal rules, authorization and test-tier discipline |
| a plugin-pipeline application | Python | Plugin-ensemble hexagon, provenance chains, content-addressed stage cache, the vet/judge layer, eval methodology, enforcement learnings |
| a schema-driven application | Python + React/TS | The three-tier decision rule, the enforcement ratchet, override policy, frontend codegen and data hooks |
| spec folders in those applications | markdown + JSON | Steering docs, EARS requirements, designs with correctness properties, wave-sequenced tasks, master sequencing, remediation tracker, handoff JSON, hooks |
| a personal knowledge workspace | Python + markdown | The second-brain setup: code, record and derived index; audience/privilege classification, fact registry, review cycle |

The applications form an **abstraction ladder**: each one is a more abstract
way to build the same hexagon, and the frameworks exist to make those
patterns the path of least resistance. `shared/05-abstraction-ladder.md`
explains the progression and how to pick a rung for a new project.

## Layout

```
shared/      language-agnostic invariants every repo obeys
  01-core-principles.md        the dependency rule, ports, adapters, composition root, errors, pipeline order
  02-schema-contract.md        JSON Schema as the domain source of truth; audit fields; x-extensions; versioning
  03-versioned-documents.md    append-only persistence semantics
  04-enforcement.md            "a rule without a check is a suggestion": ladder, ratchet, override policy
  05-abstraction-ladder.md     how the five repos relate and how to choose a level
  06-evals-and-verification.md generated-output verification: judges, provenance, gates, dev loop
  07-vertical-slice-build-and-test.md  schema → persistence → core → API → generated contract → UI → E2E, with the test at each layer
  08-data-privacy-layering.md  storage tiers, classification, audience/privilege, ownership, ReBAC, OBO, consent, encryption, audit
  09-ingestion-lifecycle.md    corpus → package: stages, scope and build plan, caching, extraction, cascade, versioning, provenance, proposals, consumer verbs, process controls
  10-ai-harness.md             LLM port and backends, model tiers, prompt versioning and layout, structured output, caching and provenance, judges
  11-operating-skills.md       the skill set that drives a pipeline: cycle driver, progress reporter, audits, skill contract
  12-code-intelligence-indexing.md GitNexus code graph and the document index as MCP tools: setup, freshness, impact gates, groups, branches

python/      Python rules (FastAPI, Pydantic, Motor/SQLAlchemy, Poetry)
  01-ddd-ports-adapters.md     the classical hexagon (entities, value objects, aggregates, use cases, ports, adapters)
  02-schema-driven-framework.md the schema-driven hexagon (tiers, registry, container, decorators, context)
  03-plugin-pipeline.md        plugin ensembles, provenance, stage cache, LLM adapters
  04-testing.md
  05-conventions.md

typescript/  TypeScript rules: frontend (01–05) and Node backend (06–11)
  01-react-hexagonal.md        domain components, application hooks, ports, adapters
  02-generated-layer.md        codegen from backend schemas, data hooks, case convention
  03-testing.md                frontend testing
  04-conventions.md            frontend and backend conventions
  05-ui-platform-rules.md      services provider, error presentation, accessibility, regulated wording, roles, mobile/PWA, i18n, embedded apps
  06-schema-driven-framework.md package levels, core contracts, registry/container/executor, validation lifecycle, driving layer, engine
  07-backend-testing.md        vitest projects, contract suites, property and architecture tests, the testing toolkit, fuzz, baselines
  08-performance.md            micro and load benchmarks, ratchet, compat, fuzz, reporting
  09-node-ddd-ports-adapters.md the classical hexagon in Node
  10-node-pipeline-and-ai-harness.md plugin ensemble, ingestion lifecycle and AI harness in Node
  11-privacy-implementation.md the eight privacy layers in Node

go/          Go rules
  01-go-hexagonal.md           the schema-driven framework: package levels, ports, container, registry, events, errors, engine
  02-conventions.md
  03-testing.md
  04-ddd-ports-adapters.md     the classical hexagon in Go
  05-pipeline-and-ai-harness.md plugin ensemble, ingestion lifecycle and AI harness in Go
  06-privacy-implementation.md the eight privacy layers in Go

second-brain/  personal knowledge-system project design
  01-project-design.md         three folders, read-only sources, fixed schema, audience vaults, fact registry, review cycle
  02-requirements-and-design.md  how research/business inputs, facts and decisions feed the spec system
  03-evidence-lifecycle.md     item lifecycle and defensibility: custody chains, manifests, exhibits, provenance, input and access tracking
  04-topics-issues-and-relationships.md  the content graph: nodes, edges, cardinality, temporal and logical tags, topics, episodes, counting rules, profiles
  05-domain-mapping.md         subject–object extraction, entity resolution, unified domain model, bindings and contracts, convergence, prefill, logic axes
  06-design-build-and-operation-brains.md  the three brains: design, build (coding agent) and operation (the shipped agent); memory taxonomy, loops, read/write policy

templates/   files a project copies in: MCP server entries, hooks, permissions, the managed CLAUDE.md block
```

## Coverage matrix

Every design exists in every language. `shared/` holds the language-agnostic
rules; the cells name the per-language idiom file.

| Design | Python | TypeScript | Go |
|---|---|---|---|
| Classical DDD + Ports & Adapters | `python/01` | `typescript/09` | `go/04` |
| Schema-driven framework | `python/02` | `typescript/06` | `go/01` |
| Plugin ensemble, ingestion lifecycle, AI harness | `python/03` | `typescript/10` | `go/05` |
| Privacy layering implementation | `python/02` §14 + `shared/08` | `typescript/11` | `go/06` |
| Testing | `python/04` | `typescript/03`, `typescript/07` | `go/03` |
| Performance | `shared/06` §8 | `typescript/08` | `go/03` benchmarks |
| Conventions | `python/05` | `typescript/04` | `go/02` |
| Frontend hexagon | — | `typescript/01`–`05` | — |

## Rule strength vocabulary

- **MUST / MUST NOT** — a correctness or integrity guarantee. Class A: never
  overridden; if it blocks you the rule or the design is wrong, raise it.
- **SHOULD / SHOULD NOT** — a strong default with real exceptions. Class B:
  overridable at the narrowest scope, with the reason at the site, and noted in
  the commit if it moves a ratcheted count.
- **MAY** — guidance.

Every MUST in these documents names, or asks you to write, the check that
enforces it. See `shared/04-enforcement.md`.

## Adopting in a repository

1. Copy or symlink the relevant language folder into the repo's
   `.claude/rules/` (or reference this folder from `CLAUDE.md`).
2. Add the project-specific layer map (which directories are core, adapters,
   composition root) as a short `hexagonal-architecture.md` that defers here.
3. Write the enforcement checks before stating the rules locally: an AST-based
   fitness test for the import rules, and a ratchet baseline for existing debt.
4. Record any Class B overrides in an allowlist with a reason per entry.
5. For a schema-driven TypeScript service, add the framework's testing
   package as a dev dependency and run its contract suites against your
   adapters.
6. Index the repo with GitNexus, copy the hook, permission and `CLAUDE.md`
   block templates, register the document index read-only, and define a
   group when the product spans repos (`shared/12`).
