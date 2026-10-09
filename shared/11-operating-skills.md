# Operating skills for a pipeline project

A long-running ingestion or AI pipeline is driven by **skills**: short,
procedural documents an agent or person follows for one stage or one
method. They replace step-by-step direction and keep the canonical commands
in one place. Generalised from the skill set of the pipeline application.

## 1. The skill set

| Kind | Skills (one each) | Purpose |
|---|---|---|
| Map | `run-<system>` | the framework map: what runs what, entry points for parse, build, vet, derive, package |
| Acquire | `source-inventory`, `corpus-prep` | inventory sources and flag acquisition gaps before extraction; audit download → convert → clean → segment → chunk and map each symptom to its stage |
| Chunk | `chunking` | the boundary layer: section-aware chunking, atomic groups, density versus size |
| Build | `run-<system>` (build) | build a package; smoke mode; cache behaviour |
| Vet | `extraction-vet`, `run-vet` | deterministic accuracy measures first; then the judge: prefilter, calibration, run and re-run, the fix loop, resilient runners, reading results |
| Audit | `pack-audit`, `plugin-review`, `<contract>-audit` | fixed-shape reports: counts versus a yardstick, run state, misses, spot checks, contract quotes with literal violations |
| Derive | `stage-dag`, `rules-cascade`, `<field>-mapping`, `<interview>-intake`, `<form>-templating` | each deterministic derived artifact and its grounding audit |
| Drive | `pipeline-cycle` | the self-driving loop: locate the stage, run its skill, check the gate, advance; stop only on a real decision |
| Report | `pipeline-progress` | where each subject is, which gates passed, what is stale, the exact next command |
| Hygiene | `reindex-check`, `gitnexus-{guide,cli,exploring,impact-analysis,debugging,refactoring}`, `karpathy-guidelines` | pre-edit index freshness; the code-graph skill family (`shared/12`); behavioural guardrails for code changes |

Review agents (architecture reviewer, plugin developer and fixer,
evaluator, package auditor, contract auditor) are the write-capable or
read-only counterparts invoked by the skills.

## 2. The skill contract

Every skill file has:

- `name` and a `description` that states what it covers and the trigger
  phrases a user would say ("is the extraction accurate", "what's next",
  "why did a chunk truncate"). The description is how the skill is found.
- Whether it is **read-only** or writes, and under what conditions.
- A "what you never do" section before "what you do" when the skill touches
  anything sensitive or irreversible.
- The commands, with exact flags, and the gate each command proves.
- Dated gotchas and validated learnings, each tied to the incident that
  produced it; a skill is where hard-won operational knowledge survives.
- Links to the one canonical reference for anything it must not restate (the
  stage list, the vocabulary, the identity rules). Restated lists are how
  docs go stale.

## 3. The cycle driver

```
locate  → read the progress reporter or run state to find the current stage
run     → the stage's skill; prefer the deterministic or local path
gate    → run the gate command (one command, pass/fail); apply known fixes from the learnings doc without escalating
advance → next stage, or next subject once every gate passes
stop    → only for a gate failing for a new reason, a decision that is the user's, or incomplete raw data (bounce to acquisition)
```

- Multi-step runs go through a committed chain script, never ad-hoc command
  lines; the chain stops on any gate failure.
- Order subjects by dependency (upstream package before dependants); a
  rebuilt upstream forces dependants to rebuild.
- When a gate stops the chain, classify before fixing: regression versus
  never-extracted versus false coverage; source, code, or prompt change
  (compare prompt hashes across versions).
- Report each turn: subject, stage just run, gate result, what advanced,
  what is running in the background, the single next action. Keep the user
  out of per-stage mechanics; surface decisions and completions.

## 4. The progress reporter

- Reads gate records and run state; never recomputes a gate.
- Marks a gate record stale when its inputs hash changed.
- Flags a changed extraction prompt before a build.
- Reports per subject: built, packaged, vetted, pass rates, stale versus
  current, and the exact commands to advance.

## 5. Rules the skills enforce

- A gate is a command with an exit code; "coverage looks rich" is not a
  gate. Prose gates were misread four times before they became commands.
- Never hand-roll a normaliser or resolver that an authority already
  provides; check the key you think you are checking.
- Search the index, not grep; count, facet, search, then show.
- Concurrency rules live in one place and every skill links to them.
- Long jobs run in the background and are resumable; killing is safe.
- Learnings are read once per session; a skill that contradicts the
  learnings doc is wrong until corrected.
