# `design.md` schema

## 1. Structure

```markdown
# Design Document: <Feature Name>
**Status:** <proposed | accepted | superseded> <date>      ← optional header lines
**Basis:** inspection of the current application …          ← what the design was verified against

## Overview
  ### What This Design Covers
  ### Design Philosophy / Key Design Decisions      numbered; each states the choice, the rejected alternative, and why
  ### Dependency on Adjacent Specs                  table: spec → relationship (consumes / feeds / amends)
  ### What Already Exists                           verified code findings; what to reuse, extend, remove
## Architecture
  ### System Context                                diagram (mermaid) of actors, layers, external systems
  ### Ownership boundaries                          concern → owner (engine, service, agents, reviewers)
  ### Data flows                                    sequence diagrams for the critical paths
## Components and Interfaces
  ### Domain Layer                                  entities, value objects, domain services, events
  ### Application Layer                             use cases, commands, responses, ports (primary/secondary)
  ### Infrastructure Layer                          adapters, persistence models, external clients
  ### Frontend Components / Application Hooks / Ports / Adapters
  ### API Endpoints                                 table: method, path, auth, request, response, status codes
## Data Models                                      (plural) schemas, migrations, invariants, indexes
## Error Handling                                   tables: scenario → status → response (backend); scenario → handling (frontend)
## Correctness Properties                           numbered; each ends with **Validates: Requirements N.M**
## Testing Strategy                                 unit, property-based, integration, E2E; libraries; what each proves
## Audit Logging                                    endpoint/action → audit event
## Access Control and Privacy                       who may do what; classification; consent gates
## Accessibility                                    WCAG level, component and page checks
## Implementation Sequence and Acceptance           phases, gates, what "done" means
## Existing Code Integration Points                 files to touch, with line-level findings when verified
## Related specs
```

Not every section applies to every spec; the first eight are expected for
any spec with implementation.

## 2. Rules

1. **Decisions are numbered and argued.** Each key decision names the
   alternative not taken and the reason (performance budget, blast radius,
   future multi-tenancy, hexagonal boundary). A later reader can disagree
   with a specific decision.
2. **Components are placed in hex layers.** Every new thing is a domain
   entity, a port, a use case, an adapter, a component, a hook, or a page; a
   design that cannot place a component is incomplete.
3. **The domain stays unaware of infrastructure.** Designs state explicitly
   when a concern (encryption, authorization, audit) is absorbed at an adapter
   boundary so entities, repositories and use cases are unchanged.
4. **Data models are concrete**: fields, types, nullability, identity, audit
   fields, indexes, migrations, and what clients may not set (server-supplied
   identity and tenancy).
5. **Error handling is a table**, keyed by scenario, with the status code and
   the exact response shape; frontend handling is a sibling table (redirect,
   alert, retry, empty state).
6. **Correctness properties** are universally quantified ("for any …"),
   machine-checkable statements that bridge requirements and tests. Each
   validates named requirement ids. Property-based tests cite the property
   number; checkpoints cite the properties they prove.
7. **Testing strategy is dual**: example-based unit tests for specific
   behaviours, property-based tests for invariants, integration tests against
   real infrastructure for execution and version guarantees, E2E for user
   journeys. Name the libraries.
8. **"What already exists" is verified against code**, with file paths and
   line references for defects found (a declared field never written, a model
   ahead of its schema). Discrepancies become tasks.
9. **Confidence is a signal, not a measure**: any design that consumes model
   confidence says how it is calibrated or that it only routes.
10. **Legal and privacy guardrails are design elements**: advice-boundary-safe wording,
    consent gates as server-side preconditions, classification-driven
    handling, audit events per endpoint.
11. **Accessibility is a section**, not a footnote: WCAG 2.1 AA, component
    axe assertions, page E2E checks, plain-language level.
12. Diagrams are mermaid, in the document; no external images.

## 3. Validation

- `## Data Models` (plural) and ports under `## Components and Interfaces`
  are format-validated.
- Every property has `Validates: Requirements …` with ids that exist.
- Every API endpoint in the table appears in a task.
- Every "to be removed" item in the code inventory appears in a task.
