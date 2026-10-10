# The spec system

## 1. Layout

```
<specs>/                       (the spec tool's folder when one owns it)
├── steering/                  durable context every agent reads first
│   ├── product.md             what the product is, who it serves, value, legal boundaries
│   ├── tech.md                stack, versions, commands, what is current vs future
│   ├── structure.md           repository and layer map, naming, file-size guidance
│   └── steering.md            (optional) development guidelines and current priorities
├── specs/
│   ├── README.md              index of specs by subsystem with status
│   ├── MASTER_SEQUENCING.md   phases, dependencies, gates, readiness vs implementation audit
│   ├── SPEC_REMEDIATION_TRACKER.md   (when reconciling) classes of divergence, READY rows
│   └── <spec-name>/
│       ├── requirements.md    EARS acceptance criteria (always)
│       ├── design.md          technical design (specs with implementation)
│       ├── tasks.md           executable, wave-sequenced plan
│       ├── standards.md       (older convention) non-functional standards; superseded by design.md
│       ├── .config.json       {"generationMode": "requirements-first"}
│       └── <auxiliary>.md     code inventory, data-model deltas, decision records, worked examples
├── handoff.json               machine-readable mirror of the tracker's READY rows
└── hooks/*.hook               on-file-change / manual / agent-stop reviewers

.claude/
├── workflows/                 feature-lifecycle, implement-spec, new-entity, pre-PR, sequencing
├── state/progress.md          living implementation state; read at start, updated before handoff
├── state/known-issues.md      gotchas, failed approaches, root causes
├── rules/                     architecture rules (this repo's per-language folders)
├── agents/ or teams/          agent definitions with ownership and workflow
└── skills/refine-spec/        refine a spec headlessly; the wave checker
```

- One spec per feature or subsystem, `kebab-case` (or `NN-kebab-case` when a
  numeric ordering helps). A spec directory is the unit of refinement,
  validation, review and execution.
- Steering is small, durable and read by every agent; specs are many and
  change often; state files change every session. Do not put session state
  in steering, and do not put rules in specs.

## 2. The lifecycle

```
research/ and business/ inputs (evidence-graded)
   → steering (product, tech, structure)
   → requirements.md   (EARS; what and why; glossary; constraints)
   → design.md         (how; hex layers; data models; properties; tests)
   → tasks.md          (phased tasks with requirement back-refs; dependency graph; waves)
   → refinement + validation (format, waves, dependency judgment)
   → MASTER_SEQUENCING.md row + handoff JSON (READY)
   → execution via the feature lifecycle (A → H), waves in order, checkpoints block
   → tasks checked off; sequencing, state files, tracker updated
   → periodic reconciliation against shipped code (remediation classes A/B/C)
```

Generation mode is **requirements-first**: no design without requirements,
no tasks without design. Tasks cite requirements; design properties validate
requirements; checkpoints name the commands that prove them.

## 3. Who writes what

- **Drafting** (an assistant or a person): requirements, design, tasks, in
  that order, from steering, research, code inventory and existing specs.
- **Refinement** (a headless spec agent): brings the three files to the
  validated format (exact titles, user-story blocks, data models, wave JSON,
  back-references), self-verifies, commits per spec, and flips the tracker
  row. One spec per run; one git worktree per concurrent run; never merge to
  main from the refinement branch.
- **Verification** (code, then judgment): the wave checker proves the wave
  graph by arithmetic; a narrow read-only auditor judges whether a dependency
  edge is missing or spurious; the native format validator runs where it is
  reachable. A self-certified READY is not trusted until tier 1 passes.
- **Execution** (the orchestrator and owning agents): reads the spec as of
  the stated commit, runs the feature lifecycle, respects wave order and hard
  gates, updates tasks and state files.
- **Reconciliation** (reviewer + orchestrator): classifies spec-vs-code
  divergence and fixes the spec first when the code is the authority.

## 4. Hooks

Hooks are tool-neutral: each is a prompt with a trigger (a glob, a manual
invocation or agent stop) and a stated check. The set below is the one
every project carries; the names are roles, and the globs are the project's
own.

| Hook role | Trigger | Does |
|---|---|---|
| architecture review | on change of `<backend source glob>` | checks layer imports (core → adapter, adapter → adapter) and logic in adapters against the per-language fitness rules |
| schema registration review | on change of `<schema file glob>` | audit fields, `title`, `version`, valid types, naming (`shared/02`) |
| frontend test runner | on change of `<frontend source glob>` | runs the co-located test, checks test ids, flags stale library patterns |
| coverage review | manual | the lowest-coverage modules and the most impactful test to write |
| state-file update | agent stop / manual | update `progress.md` and `known-issues.md` before ending |
| next-spec execution | manual | read state and sequencing, pick the next incomplete spec, start the lifecycle |

A hook is the authoring-time rung of the enforcement ladder for agents, not
a substitute for CI checks; every hook names the CI check that catches what
it missed.

## 5. Invariants of the system

1. **Specs describe; code is reality.** `MASTER_SEQUENCING` status columns mean
   spec readiness, never implementation state; the implementation audit table
   is the source of truth for what exists (Built / Partial / Stub / Mock /
   Missing, each with evidence).
2. **Every task cites requirements; every property validates requirements;
   every checkpoint names commands and pass criteria; every user story names
   its schema** (`specs/02` rule 9).
3. **Waves encode real dependencies and are never auto-generated.** A task is
   in exactly one wave; waves are contiguous; every dependency edge crosses
   to a later wave.
4. **Amendments are visible.** A spec that changes another adds an amendment
   note to the amended spec's introduction; a spec pending remediation
   carries a banner naming the tracker item; superseded files say so and point
   to the authority.
5. **One authority per fact.** Sequencing owns phases; the tracker owns
   remediation state; the handoff JSON mirrors the tracker and loses when they
   disagree; `progress.md` owns session state.
6. **Checkpoints are blocking.** A hard gate (for example "migration cycle
   green" or "authentication E2E green on an encrypted store") stops the
   wave sequence until proven, and asks the user before anything
   irreversible.
7. **Existing code is inventoried before design.** An `EXISTING_CODE_INVENTORY`
   or "What Already Exists" section prevents re-implementing shipped work and
   names what is to be removed.
