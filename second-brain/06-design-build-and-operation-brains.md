# The three brains: design, build and operation

An agentic project has three brains, not one, and they belong to three
different agents.

- The **design brain** is what the project knows about what it is building:
  why, for whom, what was decided and rejected, what is sequenced, what was
  learned. Its agent is the designing team: people, with drafting agents.
- The **build brain** is what the development agent knows while building the
  system: the codebase as a graph, the rules, where work stands, what has
  been tried, how to drive the pipeline, who owns which files. Its agent is
  the coding assistant working in the repository.
- The **operation brain** is what the system's own agent knows while it
  runs: the record it has ingested, its domain model, its facts and gaps,
  its procedures, its run and gate history, its users and their
  permissions. Its agent is the agent shipped inside the application.

Confusing them is how a project ends up with stale plans presented as
state, runtime facts baked into specs, private records in a code
repository, or a product agent that knows about the developer's open pull
request. This file defines each brain, its stores, its writers, the memory
taxonomy both agent brains share, and the loops between the three.

## 1. Side by side

| | Design brain | Build brain | Operation brain |
|---|---|---|---|
| Agent | designing team; drafting agents | the coding assistant | the application's agent |
| Question | what should exist and why | how do I build it, and where am I | what is the case, and how do I act for this user |
| Subject matter | the product, its users, its constraints | the codebase, the toolchain, the plan's state | the world the product operates on: records, entities, events, people |
| Owner | people | the development team | the product; operators and end users curate within their rights |
| Changes | per decision; reviewed | per session and per commit | per run, per ingest, per user action |
| Truth rule | decided and recorded; amendments visible | observed in the repo; derived from source; rebuilt not edited | observed, hashed, cited; corrections supersede |
| Lives in | the spec folder, research and business inputs, the rules repo | `.claude/` (state, skills, hooks, memory), indexes, learnings, CI | the application's storage tiers, registries, run store, audit |
| Freshness | stale when code reality diverges | stale when an index lags HEAD or state files lag the work | stale when a fact is superseded, a gate's inputs changed, a source re-ingested |
| Contains private data | never | never (code and process only) | yes, under the privacy layering |
| Specified in | `specs/01–05`, `02` | `shared/04`, `shared/06`, `shared/11`, `shared/12`, `specs/05` | `01`, `03`, `04`, `05`, `shared/08`, `shared/09`, `shared/10` |

The design brain is the input to the other two; the build brain produces
the system; the operation brain is produced by the system running over the
world. None is a copy of another.

The operation brain is itself *designed*: its memory schema, retention,
privacy and curation rules are requirements and design decisions in the
design brain, and its stores are built and tested by the build brain. Its
*contents* belong to operation alone.

## 2. The design brain

| Layer | Contents | Where specified |
|---|---|---|
| evidence for decisions | evidence-graded research, business and regulatory inputs | `02` §2 |
| intent | steering: product, tech, structure | `specs/05` §4 |
| requirements | EARS acceptance criteria with stable ids | `specs/02` |
| design | numbered decisions with rejected alternatives, hex-layer components, data models, correctness properties | `specs/03` |
| plan | tasks with requirement back-references, checkpoints, dependency graph, waves | `specs/04` |
| order of the plan | master sequencing and the remediation tracker | `specs/05` §1–2 |
| constraints | this rules repo and per-repo rule files that defer to it | `README.md` |
| contradictions | spec versus code, spec versus spec, spec versus rules | `shared/07` §3 |
| facts and decisions as rows | fact registry keys cited by requirements; decision records with status | `02` §3 |
| the operation brain's own design | memory schema, retention, privacy layer per memory, curation roles | this file §4, `shared/08` |

Rules: requirements first; every decision names its rejected alternative;
amendments and remediation banners are visible; status columns mean spec
readiness, never implementation state; a number in a spec is evidence for
why a rule exists, not live state.

## 3. The build brain

| Memory | Holds | Store | Written by |
|---|---|---|---|
| working | the current task: goal, plan, open questions, partial results | the session transcript and scratch files | the coding agent |
| session state | checkpoint, what changed, what is half-done, do-this-first | `progress.md`, `known-issues.md`, `HANDOFF.md`, handoff JSON | the completing agent before handoff |
| episodic | what was built and verified: commits, CI runs, gate records, benchmark baselines, dev-loop results | git history, CI artifacts, ratchet baselines, findings files | tooling, as it happens |
| semantic | what is known about the code: the rules, the layer map, the learnings, the defect classes, Class B override allowlists | the rules repo, `hexagonal-architecture.md`, learnings docs, allowlists | people; agents propose |
| procedural | how to build: skills, workflows, chain scripts, hooks, pre-commit, the cycle driver | `.claude/skills`, `.claude/workflows`, hooks, `scripts/` | people, with agents drafting; versioned and tested |
| structural | what the code is: symbols, calls, flows, routes, contracts, document chunks | code graph index, document index, schema registry | indexers; rebuilt from source |
| social | who owns what: file-ownership matrix, agent team definitions, reviewers | roster and ownership files | the development team |
| personal | durable facts about the developer and feedback on how to work with them | the agent memory directory, one fact per file, indexed | the coding agent, confirmed by the developer |

Rules of the build brain:

- **It knows the codebase, never the world.** No record content, no end-user
  data, no production facts. A privacy scan over the repository and the
  state files is a gate (`shared/08` §12).
- **Derived memory is rebuilt, not edited.** Indexes rebuild from source;
  staleness against HEAD is a bug (`shared/12` §4).
- **Session continuity is a property of the stores, not the agent.** At
  session start read the state files, run status, check index freshness,
  read the learnings once; check known issues before debugging; append a
  dead end immediately; before handoff update state and produce the
  structured summary (`shared/11` §3, `specs/05` §3).
- **Procedures are versioned and tested.** A skill or hook change is a
  commit with a dev-loop run; a skill that contradicts the learnings is
  wrong until corrected.
- **Personal memory is sparse and verified.** One fact per file with why
  and how to apply; nothing the repo already records; a memory naming a
  file or flag is checked before being acted on.

## 4. The operation brain

The same taxonomy, different subject, different stores, and every memory
sits inside the privacy layering.

| Memory | Holds | Store | Written by | Privacy |
|---|---|---|---|---|
| working | the current user task: goal, retrieved context, partial reasoning, tool results | request-scoped context; never persisted beyond the run except as provenance | the system agent | scoped to the acting principal |
| session state | a conversation or workflow in progress: open items, last checkpoint, pending confirmations | a session store with TTL and owner | the system agent | owner-scoped; expires |
| episodic | what happened: ingests, runs, stages, LLM calls, gate records, findings, user actions, access decisions | run store, custody log, audit log, findings, access log (`03` §4, `shared/08` §10) | code, as it happens; never by the model directly | append-only; dual trails |
| semantic | what is known: items and their classifications, facts with verdicts and sources, gaps with search trails, the domain model and bindings, canonical names, the content graph | storage tiers, fact and gap registries, model store, vocabulary (`01`, `03`, `04`, `05`) | code records; the model proposes; curators approve | classification tags and audience per row |
| procedural | how to act: prompts with versions, model tiers, skills exposed to users, workflows, consumer verbs, gates | prompt manifest, tier table, skill and workflow definitions, gate configs (`shared/09`, `shared/10`) | the build brain ships them; operators tune within bounds | no user data inside |
| structural | what the sources are: document chunks with citations, schemas, indexes over the record | the document index, schema registry, search indexes | indexers over the record; rebuilt | inherits the source item's classification |
| social | who is who: principals, roles, relationships, delegations, consent | identity, ReBAC tuples, delegation grants, consent ledger (`shared/08` L3–L6) | principals and administrators; never the model | audited; append-only consent |
| personal | end-user preferences and durable facts about them | a per-principal preference store | the user, or the agent with the user's confirmation | owner-only; erasable |

Rules of the operation brain:

- **Code records; the model proposes; people decide.** No memory row is
  written by the model directly; the model's output is validated against a
  schema, applied by code, and logged with provenance (`shared/10` §6).
- **Episodic memory is append-only and hashed.** Nothing is edited; a
  correction is a new record pointing at the old one.
- **Semantic memory supersedes, never deletes**, except through the erasure
  path, which is crypto-erasure of the key plus a tombstone (`shared/08`
  L7).
- **Every read is scoped.** Retrieval into working memory goes through the
  same authorization port as any other read; the agent sees what its acting
  principal may see and nothing more; cross-user leakage through a shared
  index or cache is a Class A defect.
- **Learning is a product feature, not a side effect.** What the system
  agent is allowed to remember about a user, for how long, and who can see
  it, is a requirement with an acceptance criterion and a test.
- **It knows nothing of the build.** No repository paths, developer
  identities, CI state or spec status in operation stores or prompts.

## 5. The loops between the brains

```
                 rules, specs, steering            code, procedures, prompts, config
 design brain ───────────────────────▶ build brain ───────────────────────▶ operation brain
      ▲                                    │  ▲                                   │
      │  remediation, contradictions,      │  │  findings, failure classes,       │
      │  learnings, product proposals      │  │  eval results, incidents,         │
      └────────────────────────────────────┘  └───────────────────────────────────┘
```

| Flow | Carrier | Rule |
|---|---|---|
| design → build | requirements, design decisions, tasks, rules | the build agent obeys; it does not reinterpret the spec |
| build → design | remediation rows with class and evidence, contradiction reports, learnings | reviewed promotion; status is corrected to match validated reality before gaps become work (`specs/05` §2) |
| build → operation | releases: code, prompt manifest versions, tier tables, skills, gate configs, schema versions | nothing reaches operation except through a tested release; config carries its version |
| operation → build | findings with producer layer and rerun command, failure classes, eval results, incident records, performance baselines | land as rows first; become bugs, tests and learnings; never edit the operation brain to make a finding go away |
| operation → design | growth reports, synonym proposals, usage evidence, requirement change requests | evidence-graded like any other input (`02` §2); the model proposes, a person decides |
| operation → operation | curation: verdicts, canonical-name merges, binding approvals, tag corrections | by curators within their rights; logged |

Which brain yields when they disagree follows the remediation classes: when
the running system is the validated authority, the design is wrong; when
the design is ahead, the build has backlog; when they genuinely disagree in
the application layer, shipped-and-tested code is the default and the
divergence is recorded.

## 6. Agent read and write policy

| Store | Build agent | System agent | Human commits |
|---|---|---|---|
| steering, requirements, design, rules | read; propose amendments | no access | yes |
| tasks, sequencing, tracker, handoff JSON | read; check off with evidence | no access | review |
| progress, known issues, handoff | read and write at checkpoints | no access | no |
| skills, workflows, prompts, hooks | read; draft with manifest bump and tests | read the released version only | review |
| code graph and document index of the repo | read; rebuild via the indexer | no access | no |
| record originals, custody logs | no access (fixtures only) | read within scope; never write | never (write-once by code) |
| facts, gaps, bindings, vocabulary | fixtures only | propose rows; code applies validated rows | curation |
| audit, run store, gate records (operation) | read aggregates for evals | written through recording code paths only | never by hand |
| identity, ReBAC, consent | fixtures only | read through the authorization port; never write | administrators and principals |
| developer memory | one verified fact per file | no access | the developer confirms feedback |
| end-user preferences | no access | read and write for the acting principal only | the user |

Every non-proposal write by either agent carries actor type, reason and
inputs hash (`shared/08` §10). An agent proposes and simulates; a human
commits anything consequential (`shared/09` §11).

## 7. Tests and gates

| Concern | Check |
|---|---|
| state in the wrong brain | dated status lines in steering or rules fail a test; numbers in prose that are not fact-registry references fail a lint |
| world data in the build brain | privacy scan over the repository, state files, fixtures and agent memory finds no classified or personal content |
| build data in the operation brain | prompts, configs and stores contain no repository paths, developer identities or spec status; a release-content test asserts it |
| handoff completeness | the orchestrator rejects a handoff missing the summary or state-file updates |
| episodic integrity | custody and audit chains replay; run store rows are never updated in place |
| procedural drift | prompt manifest hashes; released version equals the manifest; skills checked against learnings; no bypass flags |
| structural freshness | indexed commit equals HEAD before edits; operation indexes marked stale on source change |
| scoped retrieval | a cross-principal retrieval test fails on any leaked row; shared caches key on principal and classification |
| memory as a requirement | every operation memory has a retention, an owner, a privacy layer and an erasure test |
| loop closure | every finding has a producer layer and a rerun command; every remediation row names its class and evidence; every learning names its incident |
| memory hygiene | one fact per developer-memory file with type and why; one index line per file; no repo-derivable facts |
