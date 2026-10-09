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

python/      Python rules (FastAPI, Pydantic, Motor/SQLAlchemy, Poetry)
  01-ddd-ports-adapters.md     the classical hexagon (entities, value objects, aggregates, use cases, ports, adapters)
  02-schema-driven-framework.md the schema-driven hexagon (tiers, registry, container, decorators, context)
  03-plugin-pipeline.md        plugin ensembles, provenance, stage cache, LLM adapters
  04-testing.md
  05-conventions.md

typescript/  React + TypeScript rules
  01-react-hexagonal.md        domain components, application hooks, ports, adapters
  02-generated-layer.md        codegen from backend schemas, data hooks, case convention
  03-testing.md
  04-conventions.md

go/          Go rules (stellar-drive)
  01-go-hexagonal.md           package levels, ports, container, registry, events, errors, engine
  02-conventions.md
  03-testing.md

second-brain/  personal knowledge-system project design
  01-project-design.md         three folders, read-only sources, fixed schema, audience vaults, fact registry, review cycle
  02-requirements-and-design.md  how research/business inputs, facts and decisions feed the spec system
```

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
