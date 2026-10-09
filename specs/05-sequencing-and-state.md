# Sequencing, reconciliation, handoff and state

## 1. `MASTER_SEQUENCING.md`

The one authority for implementation order.

```markdown
# Master Spec Sequencing Plan
## Purpose
> READ THIS FIRST — "Status" means SPEC readiness, not IMPLEMENTATION status. Use the audit table for reality.
## Implementation Status Audit (<date>)
| Area | Spec phase | Reality | Evidence |          Built / Partial / Stub / Mock / Missing, with file-level evidence
## Phase 0: Fix Critical Integration Breaks (DO FIRST)   bugs in existing wiring, not features; each with status + resolution
## Dependency Graph                                       phases, what each spec depends on and produces, gates, independent tracks
## Detailed Sequencing with Spec Status
### Phase N: <name>
| # | Spec | Requirements | Design | Tasks | Status |
**Depends on**, **Produces**, **Purpose**, gate notes, dated status updates
```

Rules:

- Phases are ordered by architectural dependency: foundation (auth, admin
  shell) → core engines (backend-first) → modular content → engines over
  content → validation milestone with real data → user journeys → documents
  and transactions → professional portals → research and polish → tenancy and
  access control → multi-org → admin integration → marketplace. Independent
  tracks (infrastructure, payments, notifications, mobile, docs) run
  alongside.
- A **validation milestone** with real data gates the user-facing phases; it
  produces counted artifacts and a test suite covering every requirement.
- Gate changes are dated decisions with who decided; descoping records the
  reason and where the capability moved.
- Reality tables are updated in the same change that ships the feature.
  Stale counts are corrected with a dated "Was → Now" table rather than
  silently rewritten.
- Spec merges and deprecations are recorded in the phase table.

## 2. `SPEC_REMEDIATION_TRACKER.md` and `handoff.json`

When specs were authored outside the validated workflow, or have drifted from
code, a tracker reconciles four sources of truth: specs, shipped features,
prototypes, and tests (the persona-driven E2E suite is often the most current
evidence).

Divergence classes, decided **before** any remediation:

| Class | Meaning | Action |
|---|---|---|
| A — authoritative upstream | the spec disagrees with a validated pipeline or data contract the code already works against | the spec is wrong; update it; no code change, no decision |
| B — app-layer divergence | the shipped design differs from the spec with no authoritative upstream | shipped-and-tested code is the default reference; record the divergence visibly; rewrite the spec to the delivered architecture |
| C — spec ahead of code | normal backlog | status accuracy only, so the runner does not re-implement shipped work |

Posture: bring specs to match validated reality first; only then treat gaps
in reality as work items.

**READY protocol.** A row is `✅ READY` only when all of: the three files
exist and pass format validation with zero errors (warnings listed), the
wave JSON is valid (every task in one wave, waves 1-based sequential), and
the content is reconciled against shipped code. Row format:

```
✅ READY @ <short-sha> (<branch>); waves validated (<N> tasks / <M> waves)
```

`🔄 In progress` means do not start. The commit is the SHA at which **that
spec** was finalized, not branch HEAD. Implementing agents fork their own
branch from the docs branch; the docs branch is not merged to main during
remediation.

**`handoff.json`** mirrors the tracker; the table wins on disagreement and
both are updated together.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SpecHandoff",
  "type": "object",
  "required": ["generated", "authoritative_source", "specs"],
  "properties": {
    "$comment": {"type": "string"},
    "generated": {"type": "string", "format": "date"},
    "authoritative_source": {"type": "string"},
    "docs_branch": {"type": "string"},
    "docs_branch_base": {"type": "string"},
    "implementing_agent_rule": {"type": "string"},
    "specs": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["spec", "phase", "status", "branch", "commit", "waves_validated", "tasks", "waves", "validator"],
        "properties": {
          "spec": {"type": "string"},
          "phase": {"type": "string"},
          "status": {"enum": ["ready", "in_progress", "blocked"]},
          "branch": {"type": "string"},
          "commit": {"type": "string", "pattern": "^[0-9a-f]{7,40}$"},
          "waves_validated": {"type": "boolean"},
          "tasks": {"type": "integer", "minimum": 0},
          "waves": {"type": "integer", "minimum": 0},
          "validator": {
            "type": "object",
            "required": ["requirements", "design", "tasks"],
            "properties": {
              "requirements": {"enum": ["clean", "warnings", "errors", "missing"]},
              "design": {"enum": ["clean", "warnings", "errors", "missing"]},
              "tasks": {"enum": ["clean", "warnings", "errors", "missing"]}
            }
          },
          "accepted_warnings": {"type": "array", "items": {"type": "string"}},
          "hard_gate": {"type": "string"}
        },
        "additionalProperties": false
      }
    }
  }
}
```

Consumers poll `specs[]` and act only on `status == "ready"`.

## 3. State files

- **`progress.md`**: last updated (date, phase, by whom), a session
  checkpoint (spec, phase, next task), dated entries of what was delivered
  with commits and evidence (suite counts, gate results), decisions made,
  patterns established, deferred items. Read at session start; updated
  before every handoff; a handoff without it is rejected.
- **`known-issues.md`**: symptom-first entries with severity, root cause,
  fix or workaround, and "failed approaches" so dead ends are not
  re-investigated. Check before debugging; append the moment a dead end is
  found.
- Both are owned by the orchestrator role; completing agents write their own
  entries.

## 4. Steering documents

| File | Must contain | Must not contain |
|---|---|---|
| `product.md` | what the product is, personas, value propositions, legal boundaries, the core workflow | implementation status |
| `tech.md` | stack with versions, architecture, what is current versus future (say "not yet integrated"), commands per app, dev tools | rules that belong in `.claude/rules` |
| `structure.md` | repo map, hex layer map per app, naming conventions, file-size guidance, config files | task lists |
| `steering.md` (optional) | development guidelines, current priorities, quality standards | per-session state |

Steering is read first by every agent and kept short enough to be read
whole.

## 5. Team and agent definitions

- Each agent or team member has a role, a workflow paragraph (what to read
  first, which rules apply, which files it owns, how it verifies before
  handoff), and read-only versus write scopes. Reviewer, security and
  compliance roles are read-only.
- The file-ownership matrix and the shared-file protocol (`dependency
  container`, `main`, `enums`, `ServiceFactory`, `App.tsx`, `conftest`) are
  rules, not suggestions; an agent escalates instead of editing a file it
  does not own.
- Domain-expert roles (regulatory, compliance, UX research, product, business) sit
  in the team to validate content, not to write code.

## 6. Research and business inputs

Requirements draw on `research/` and `business/` folders that are
themselves evidence-graded (primary documents downloaded and extracted;
dated updates that supersede earlier sections; questions that are phone
calls, not desk research). The second-brain rules apply to them:
verify before use, name the population behind every number, supersede
visibly. See `second-brain/02-requirements-and-design.md`.
