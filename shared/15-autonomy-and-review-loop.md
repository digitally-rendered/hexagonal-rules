# Autonomy and the review loop for agents on each brain

An agent earns autonomy per brain, per edit surface and per metric; it is
never granted as a mode. This file fixes the levels, the loop contract an
agent runs at each level, what each of the three brains (`shared/14`) lets
its agent do unattended, how an agent is promoted and demoted, and what the
human reviews. Two patterns shape it: the unattended research loop (a
standing-instructions file, a confined edit surface, one metric, keep the
change if the metric improves else revert, log every experiment) and the
knowledge-wiki lint (a periodic pass that hunts contradictions, stale
claims and orphans, and proposes what to do next). The human is the editor
of every brain: people set the instructions, approve, correct and promote;
agents draft, run and log.

## 1. Autonomy levels

| Level | Name | The agent may | Gate before it counts | Logged as | Revoked when |
|---|---|---|---|---|---|
| 0 | advise | read; answer; explain | none | query | never |
| 1 | propose | produce a patch, row or draft that a human or the tooling applies | validation of the proposal's schema | proposal | never |
| 2 | apply with review | apply on a branch or in a sandbox; a human merges or a review window passes with no objection | the surface's gate command passes | experiment, kept or reverted | one unreviewed defect reaches main |
| 3 | auto-commit within bounds | apply and commit on the allowed paths when the metric does not regress | gate passes and metric non-decreasing | experiment plus commit | any revert caused by the agent, a Class A gate failure, a write outside the surface |
| 4 | unattended loop | run level 3 repeatedly for a fixed budget without a human present | as level 3, plus the stop conditions | one experiment row per iteration | as level 3, or the budget is exhausted |

A level is held for one `(agent, brain, surface)` triple. The same agent may
be at level 4 on a benchmark file and level 1 on the spec folder.

## 2. The loop contract

Every agent operating above level 1 runs under a **program file**, a
human-written standing-instructions document checked into the brain it
acts on. Nothing in it is inferred by the agent.

| Field | Content | Check |
|---|---|---|
| `goal` | one sentence; what better means | present |
| `metric` | one command, deterministic, numeric or pass/fail; self-reported signals never count (`shared/06`) | the command run twice on the same inputs gives the same value |
| `surface` | allowlist of paths or stores the agent may write; everything else is a proposal | pre-write hook denies writes outside it; CI asserts changed files are a subset |
| `forbidden` | actions never taken regardless of metric: deleting tests, weakening gates, touching generated output by hand, writing identity or consent, bypass flags | the hook denies; a violation demotes |
| `budget` | iterations, wall time, cost ceiling | the loop stops at the first exceeded |
| `stop` | conditions that end the loop early: the same failure N times, N no-gain iterations, a Class A gate failure, an attempted out-of-surface write, a stop file present | each is a test on the loop driver |
| `log` | path of `experiments.jsonl` | one row per iteration, rows equal iterations |
| `level` | the level granted, by whom, on what date, with the evidence rows | present when level ≥ 2 |

Each iteration: read the program file, make one change inside the surface,
run the gate and the metric, keep if the metric improved or held and the
gate passed, otherwise revert completely, and append the row:

```json
{"run_id":"…","started":"…","program_hash":"…","inputs_hash":"…","diff_hash":"…",
 "metric_before":0,"metric_after":0,"gate":"pass|fail","kept":true,
 "reason":"…","cost":{"tokens":0,"seconds":0},"actor":{"type":"agent","model":"…","prompt_version":"…"}}
```

A loop that cannot say what it changed, what it measured and why it kept
the change has no standing to keep it.

## 3. What each brain allows

### Design brain

| Surface | Max level | Metric or gate | Loop |
|---|---|---|---|
| research compile pages (`specs/06` §2a) | 3 | compiled page cites only raw hashes; lint finds no contradiction | compile → lint → file |
| draft spec files on the agent's branch | 2 | readiness validators and the wave checker pass; EARS parse; every story names its schema | draft → validate → propose merge |
| tasks and waves | 2 | wave checker; dependency edges cross to later waves | as above |
| tracker rows | 2 | READY only after the validators pass (`specs/01` §3) | flip with evidence |
| steering, rules, decision records | 1 | none for the agent; the editor decides | proposal only |

The design brain never reaches level 4: a design decision is a human act.
The agent's unattended work here is compile and lint, not deciding.

### Build brain

| Surface | Max level | Metric or gate | Loop |
|---|---|---|---|
| state files (progress, known issues, handoff) | 3 | handoff completeness check | write at checkpoints |
| feature code and tests under the task's paths | 2 default | the gate ladder (`shared/04`): fitness tests, suites, ratchet non-increasing, parity | the vertical slice (`shared/07`) |
| known fixes from the learnings document | 3 once proven | same gate; the fix class is listed in the learnings | apply → gate → commit |
| one confined performance or quality file with a ratchet | 4 | the benchmark or ratchet command (`shared/06` §8) | the unattended loop |
| generated output | 0 by hand; via `generate` only | drift check | regenerate |
| skills, hooks, prompts | 2 | manifest hash bump, dev loop run | propose with tests |

**Proven** has one meaning: N consecutive iterations at level 2 on the same
surface with the gate passing, zero reverts and zero escalations, where N
is a number the repository commits in its program file and never lowers
without a decision record.

### Operation brain

| Surface | Max level | Metric or gate | Loop |
|---|---|---|---|
| fact, gap, binding and vocabulary rows | 1 | schema validation; a curator applies (`shared/14` §6) | propose |
| compiled wiki pages and the index (`second-brain/01`) | 3 | links resolve; citations resolve to items; lint clean | compile → lint |
| prompt and extractor variants in an eval sandbox | 4 | the eval suite with judges and a coverage floor (`shared/06`), golden chunks, parity | the unattended loop, results as proposals to the prompt manifest |
| curation of canonical names, merges, tags | 1 | curator role | propose |
| user-facing records, identity, consent, audit | 0 | never written by the agent | none |
| end-user preferences | 2 for the acting principal only | the user's confirmation | write with consent |

The operation agent's level 4 runs only in a sandbox over fixtures and
evaluation sets, never over live records, and its output is a proposal to
release a new prompt or extractor version through the build brain.

## 4. Promotion and demotion

- **Earned, not configured.** Promotion from level k to k+1 on a surface
  requires the proven condition at level k and a human grant recorded in
  the program file with the evidence rows. Promotion never skips a level.
- **Demotion is automatic** on the conditions in §1 and is recorded in
  the same place with the triggering row; the agent continues at the lower
  level. Re-promotion starts the count again.
- **A new surface starts at level 1** regardless of the agent's level
  elsewhere. A new model or prompt version resets the count on every
  surface it touches, because the thing that earned the level no longer
  exists.
- **A kill switch** exists per loop: a stop file or flag the driver checks
  every iteration; its presence halts within one iteration and is logged.

## 5. What the human reviews, and when

| Cadence | The editor reads | Decides |
|---|---|---|
| per session | the handoff summary and the experiments rows since last session | nothing is hidden; reverts explained |
| per cycle | the lint report of the brain: contradictions, stale claims, orphans, broken links, next-question proposals | which proposals become rows, specs or tasks |
| per promotion request | the evidence rows and the program file | grant or refuse |
| per release | eval report, parity, privacy scan, the audit sample | ship or hold |
| on demotion | the triggering row and the diff | correct the surface, the program or the learnings |

Review is of the log and the lint, not of every change; that is what the
levels buy. What review finds flows back as learnings, decision records and
remediation rows (`shared/14` §5), never as silent edits to the brain.

## 6. Cross-brain rules

- An agent holds a level per brain; no loop writes to two brains. The build
  agent does not write facts; the operation agent does not write specs; the
  design agent does not commit code.
- A loop's outputs cross a brain boundary only as proposals or releases
  (`shared/14` §5).
- Program files are design-brain documents (they are decisions) even when
  they govern the build or operation agent; an agent never edits its own
  program file.

## 7. Tests

| Concern | Check |
|---|---|
| program file | schema-validated; `metric`, `surface`, `budget`, `stop`, `log` present; level ≥ 2 has grant evidence |
| surface enforcement | pre-write hook denies out-of-surface writes; CI fails an agent commit whose changed files are not a subset of the surface |
| metric determinism | the metric command run twice on fixed inputs returns the same value |
| revert | a test injects a regressing change and asserts a full revert and a `kept: false` row |
| log completeness | rows equal iterations; every kept commit references its row id |
| stop conditions | each condition has a driver test; the kill switch halts within one iteration |
| promotion | a promotion without N evidence rows fails validation; a demotion trigger produces a record |
| self-report | a loop whose metric reads the agent's own success claim fails review (`shared/06`) |
| cross-brain | an agent write to another brain's store outside a proposal fails closed |
| no bypass | program files and drivers have no flag that skips the gate or the metric |
