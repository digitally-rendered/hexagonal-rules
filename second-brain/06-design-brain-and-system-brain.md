# The design brain and the system brain

An agentic project has two brains. The **design brain** is what the project
knows about what it is building: why, for whom, what was decided, what was
rejected, what is sequenced, what was learned. The **system brain** is what
the running system knows while it operates: the record it has ingested, its
domain model, its procedures, its run history, its indexes, its session
memory. They have different owners, different rates of change and different
truth rules; confusing them is how a project ends up with stale plans
presented as state, or runtime facts baked into specs. This file defines
both, how they are stored, who may write to each, and the loop between them.

## 1. Side by side

| | Design brain | System brain |
|---|---|---|
| Question it answers | what should exist and why | what is the case right now, and how do I act |
| Owner | people, with agents drafting | the running system, with people curating |
| Changes | per decision; reviewed | per run, per session, per ingest |
| Truth rule | decided and recorded; amendments visible | observed, hashed, cited; corrections supersede |
| Primary stores | `research/`, `business/`, steering, specs (requirements, design, tasks), sequencing, decision records, contradiction reports, the rules repo, learnings | the record (`03`), the domain model and bindings (`05`), the graph (`04`), facts and gaps, skills, run store and gate records, findings, indexes, session state and memory |
| Freshness | stale when code reality diverges; reconciled by the remediation classes (`specs/05`) | stale when an index lags HEAD, a gate record's inputs changed, or a fact is superseded |
| Reader at runtime | agents read it to know constraints and intent | agents read it to know facts, procedures and state |
| Writer at runtime | agents write proposals, findings, learnings; people commit | code records; the model proposes; people curate |

The design brain is the input to the code and the rules; the system brain
is produced by the code running over the world. Neither is a copy of the
other.

## 2. The design brain

Already specified across this repo; listed here as one store:

| Layer | Contents | Where specified |
|---|---|---|
| evidence for decisions | evidence-graded research, business and regulatory inputs | `02` §2 |
| intent | steering: product, tech, structure | `specs/05` §4 |
| requirements | EARS acceptance criteria with stable ids | `specs/02` |
| design | numbered decisions with rejected alternatives, hex-layer components, data models, correctness properties | `specs/03` |
| plan | tasks with requirement back-references, checkpoints, dependency graph and waves | `specs/04` |
| order and state of the plan | master sequencing, remediation tracker, handoff JSON, progress and known-issues | `specs/05` |
| constraints | this rules repo; per-repo rule files that defer to it | `README.md` |
| learnings | validated findings per layer, the defect classes, the dev-loop discipline | `shared/06` |
| contradictions | spec versus code, spec versus spec, spec versus rules, resolved or escalated | `shared/07` §3 |
| facts and decisions as rows | fact registry keys cited by requirements; decision records with status | `02` §3 |

Rules of the design brain: requirements-first; every decision names its
alternative; amendments and remediation banners are visible; status columns
mean spec readiness, never implementation state; counts in documents are
evidence of why a rule exists, not live state.

## 3. The system brain: a memory taxonomy for an agentic system

| Memory | Holds | Store | Written by | Lifetime |
|---|---|---|---|---|
| **working** | the current task: goal, plan, open questions, partial results | the session transcript and scratch files | the agent | one session |
| **session state** | where work stands for the next session: checkpoint, what changed, what is half-done, do-this-first | `progress.md`, `HANDOFF.md`, handover log | the completing agent, before handoff | until superseded |
| **episodic** | what happened: runs, stages, LLM calls, misses, gate records, findings, verdicts, audit entries | run store, gate records, findings JSONL, audit log, custody log | code, as it happens | permanent, append-only |
| **semantic** | what is known: facts with verdicts and sources, gaps with search trails, the domain model and bindings, canonical names, the content graph | fact and gap registries, model DB, bindings files, vocabulary module | code records; model and people propose; people curate | permanent, versioned, superseded never deleted |
| **procedural** | how to act: skills, workflows, chain scripts, gates, prompts with versions, model tiers | `.claude/skills`, `.claude/workflows`, scripts, prompt manifest, tier table | people, with agents drafting; versioned with tests | per version |
| **structural** | what the code and documents are: symbols, calls, flows, routes, contracts; document chunks with citations | code graph index, document index, schema registry | indexers, rebuilt from source | until HEAD or sources change |
| **social** | who is who: roles, ownership, authority, delegations | roster, file-ownership matrix, team definitions, authorization records | people; delegations by principals | per change, audited |
| **personal / preference** | durable facts about the user and feedback on how to work | the agent memory directory: one fact per file with type `user`, `feedback`, `project`, `reference`, indexed by `MEMORY.md` | the agent, with the user's confirmation for feedback | until found wrong |

Rules:

- **Each memory has one store and one writer path.** Session state is not
  kept in steering; facts are not kept in prose; procedures are not kept in
  transcripts.
- **Episodic memory is append-only and hashed.** Nothing is edited; a
  correction is a new record pointing at the old one.
- **Semantic memory is curated.** The model proposes rows; code validates,
  applies and logs; people review; the registry key is referenced by other
  documents rather than the value restated.
- **Procedural memory is versioned and tested.** A prompt or skill change
  is a commit with a manifest bump and a dev-loop run; a skill that
  contradicts the learnings is wrong until corrected.
- **Structural memory is derived and must be fresh.** Indexes rebuild from
  source; staleness is a correctness bug; gates check the indexed commit
  against HEAD (`shared/12`).
- **Personal memory is sparse and verified.** One fact per file, with why
  and how to apply; recalled memories are background, not instructions; a
  memory naming a file or flag is checked before being acted on; nothing the
  repo already records is memorised.

## 4. Session boundaries and handoff

An agent session is stateless; continuity is a property of the stores.

- **At session start**: read the session state (progress, handoff, known
  issues), run the status step of the operating cycle (`shared/11` §3),
  check structural freshness, read the learnings once.
- **Before debugging**: check known issues and the gap log; someone may have
  hit it.
- **On a dead end**: append to known issues immediately, not at handoff.
- **Before handoff**: update session state with what was built, decided and
  established; record new issues; produce the structured handoff summary
  (files, wiring, contract, assumptions, known issues, verification
  evidence). A handoff without these is rejected.
- **At session end**: the agent-stop hook asks for the state-file update;
  the completing agent writes it, never a separate agent.

## 5. The loop between the two brains

```
design brain ──rules, specs, steering──▶ code and procedures
                                              │
                                              ▼ runs
system brain ◀──records, findings, run state── the running system
      │
      │ reconciliation: remediation classes, learnings, contradiction reports,
      │ growth reports, synonym proposals, defect classes
      ▼
design brain (amended, dated, with the evidence that forced the change)
```

- **Design → system** is one-directional through code and procedures: an
  agent at runtime obeys the rules and skills; it does not reinterpret the
  spec.
- **System → design** is a reviewed path: findings, failure classes, growth
  and synonym proposals, contradiction reports and audit results are
  recorded as rows and then promoted into specs, rules and learnings by a
  person (or an auto-commit policy that has earned it). Spec status is
  corrected to match validated reality first; only then are gaps in reality
  treated as work.
- **The remediation classes** (`specs/05` §2) decide which brain yields:
  when the running system is the authority (a validated pipeline, a shipped
  contract), the design is wrong; when the design is ahead, the system has
  backlog; when they genuinely disagree in the application layer, the
  shipped-and-tested code is the default and the divergence is recorded.
- Learnings documents are the long-term memory of the loop: validated
  findings with root cause, fix and evidence, read once per session, and
  the only place a defect class is allowed to be stated as a rule before a
  check exists.

## 6. Agent read and write policy

| Store | Agent may read | Agent may write | Human commits |
|---|---|---|---|
| steering, requirements, design, rules | always | drafts and amendments as proposals | yes |
| tasks, sequencing, tracker, handoff JSON | always | check off completed tasks; update status rows with evidence | review |
| progress, known issues, handoff | always | yes, at checkpoints and before handoff | no |
| record originals, custody logs | read-only | never | never (write-once by code) |
| facts, gaps, bindings, vocabulary | always | proposals; validated rows through the tooling | curation |
| skills, workflows, prompts | always | drafts with manifest bump and tests | review |
| indexes | always | rebuild via the indexer only | no |
| audit, run store, gate records | always | through the recording code paths only | never by hand |
| user and feedback memory | background context | one verified fact per file | the user confirms feedback |

Every agent write that is not a proposal carries actor type, reason and
inputs hash into the audit layer (`shared/08` §10); an agent proposes and
simulates, a human commits anything consequential (`shared/09` §11).

## 7. Tests and gates

| Concern | Check |
|---|---|
| state in the wrong store | a test fails on dated status lines in steering or rules; a lint flags numbers in prose that are not fact-registry references |
| handoff completeness | the orchestrator rejects a handoff missing the summary or state-file updates |
| episodic integrity | custody and audit chains replay; run store rows are never updated in place |
| procedural drift | prompt manifest hashes; skill contradiction check against learnings; chain scripts have no bypass flags |
| structural freshness | indexed commit equals HEAD before edits; gate records marked stale on input change |
| loop closure | every finding row has a producer layer to fix and a rerun command; every remediation row names its class and evidence; every learning names its incident |
| memory hygiene | one fact per memory file with type and why; an index line per file; no repo-derivable facts |
