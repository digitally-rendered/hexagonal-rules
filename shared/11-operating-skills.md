# Operating skills for a pipeline project

A long-running ingestion or AI pipeline is driven by **skills**: short,
procedural documents an agent or person follows for one stage or one
method. They replace step-by-step direction and keep the canonical commands
in one place. Generalised from the skill set of the pipeline application.

## 1. The skill set

One skill per **role** below; a project names its skills as it likes (the
names here are placeholders, not an inventory to copy), but every role has
exactly one skill and every skill fills exactly one role. Check: a test
lists `.claude/skills/*/SKILL.md`, reads the `role` field in each
frontmatter and fails on a missing or duplicated role.

| Role | Skill (placeholder) | Purpose |
|---|---|---|
| Map | `run-<system>` | the framework map: what runs what, entry points for parse, build, vet, derive, package |
| Acquire | `source-<kind>` (one per source kind), `corpus-prep` | inventory sources and flag acquisition gaps before extraction; audit download → convert → clean → segment → chunk and map each symptom to its stage |
| Chunk | `chunking` | the boundary layer: section-aware chunking, atomic groups, density versus size |
| Build | `run-<system>` (build) | build a package; smoke mode; cache behaviour |
| Vet | `vet-<measure>` | deterministic accuracy measures first; then the judge: prefilter, calibration, run and re-run, the fix loop, resilient runners, reading results |
| Audit | `audit-<subject>` | fixed-shape reports: counts versus a yardstick, run state, misses, spot checks, contract quotes with literal violations |
| Derive | `derive-<artifact>` (one per deterministic derived artifact) | the derived artifact and its grounding audit |
| Drive | `<system>-cycle` | the self-driving loop: locate the stage, run its skill, check the gate, advance; stop only on a real decision |
| Report | `<system>-progress` | where each subject is, which gates passed, what is stale, the exact next command |
| Hygiene | `reindex-check`, the `gitnexus-*` family, `knowledge-maintenance` | pre-edit index freshness; the code-graph skill family (`shared/12`); the compiled-knowledge rules of §1a |

Review agents (architecture reviewer, plugin developer and fixer,
evaluator, package auditor, contract auditor) are the write-capable or
read-only counterparts invoked by the skills; they are roles too, and the
same uniqueness test covers `.claude/agents/`.

### 1a. The `knowledge-maintenance` skill

The one skill that states how a brain's compiled knowledge is kept honest,
following the LLM-Wiki pattern as `second-brain/01` makes it strict. It is
read by every agent that ingests, compiles, queries or lints a brain, and
it holds no record facts. Its contract:

- **ingest**: raw sources are immutable and hashed before anything reads
  them; an ingest proposes rows and compile changes, never edits raw.
- **compile**: compiled pages (`wiki/`) are regenerated from rows and
  marked generated; the index page and related pages are touched in the
  same pass; the LLM proposes the compile, code applies and renders it
  (`second-brain/01` §4a).
- **query**: an answer is filed back as a cited page or a gaps row, with a
  `query` op in the log (`second-brain/01` §7).
- **lint**: deterministic lint first (contradictions, broken links, orphan
  pages, stale claims, concepts without a page), then an LLM pass that only
  proposes next questions into `gaps.jsonl` (`second-brain/01` §11).
- **log**: every op is one row of the closed enum in the brain's one
  `log.md` (`second-brain/01` §11); the skill never writes a second log.

Check: the skill file exists in every project that has a brain, its
sections are exactly these five, and a test asserts each named check
command in it exits 0 on the fixture brain.

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
