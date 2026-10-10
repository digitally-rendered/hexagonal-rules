# Second-brain extension: requirements input and design

The second brain (`01-project-design.md`) is a verified, citable record built
from scattered sources. The spec system (`specs/`) is the same discipline
applied to **what to build**: research and business inputs become steering,
requirements, designs and tasks, and the record of decisions survives
sessions. This file states how the two join.

## 1. The same four tiers

| Second brain | Spec system |
|---|---|
| originals by hash (`archive/`) | primary sources: downloaded regulator reports, statutes, prior specs, code inventory at a commit |
| configs and working notes (`data/`, `working/`) | `research/`, `business/`, steering, the specs folder |
| derived, rebuildable (`<index>/`) | generated schemas, wave checks, status audits, evidence bundles |
| private, local-only | credentials, keys for spec agents, unreleased financials |

Code lives apart from the record in both: the rules and tools repo holds no
private or business facts; the spec repo holds no secrets.

## 2. Evidence-graded inputs

- A research document opens with an **evidence quality** note: which sources
  are primary (downloaded, extracted, dated), which are secondary, and what
  cannot be known from the desk. Verbatim-grounded claims are marked as such.
- Dated **updates supersede** earlier sections in place ("read these
  corrections first; where they conflict with anything below, these win"),
  never by silent rewrite.
- Every number names its population and denominator.
- A prediction is not a finding; a finding that drives a requirement carries
  its citation into the requirement's introduction.
- Decisions (corporate structure, gates, descopes) are small decision
  records: date, status, context, decision, consequences.

## 3. Facts, decisions and requirements as rows

- Key figures used in requirements (thresholds, limits, dates, counts from a
  data pipeline) live in a **fact registry** row with source and verdict, and
  requirements reference the key rather than restating the number. When the
  fact is corrected, every requirement that cites it is found by key.
- Requirement ids are stable identifiers; design properties and tasks cite
  them the way claims cite evidence ids.
- Amendments to a requirement are new rows: the old criterion stays, the
  amendment carries a date and a reason, and the sequencing or tracker names
  who decided.
- A spec's "What already exists" section is the equivalent of verify-before-
  use: inspect the code at a stated commit, record findings with file and
  line, and label each as built / partial / stub / mock / missing.

Requirement rows carry a `schema` column (the entity, view or operation the
story names, per `specs/02` rule 9) so the fact registry, the requirement
and the generated surfaces share one key; a fact cited by a criterion about
data shape lives in the schema's `x-*-reason` text, not restated in prose.

## 4. Audience and privacy for specs

- Steering and most specs are internal. Trust and accessibility statements,
  public runbook summaries and the product README are the only artifacts
  linked from a public surface; everything else is linked from nowhere public.
- Research that quotes regulators or funders is kept with its source
  documents; personal data in research (named individuals) follows
  the second brain's audience rules and is not copied into specs.
- Secrets for headless spec agents come from the keychain at runtime, are
  never hardcoded in skills, and are rotated if ever pasted in plaintext.

## 5. The review cycle for specs

```
status   → sequencing audit, tracker rows, uncommitted spec edits, stale "Produced" counts
collect  → new research, new regulator text, new code reality (commit SHA)
verify   → wave checker on changed tasks, format validation, dependency judgment, code inventory re-check
review   → classify divergence (A/B/C); fix the spec first where the code is the authority
record   → sequencing rows, tracker rows, handoff JSON, state files, decision records
hand off → progress.md session checkpoint; "do this first next session" when something is broken
```

Quality gates before a spec is marked ready: exact titles and blocks; every
criterion in EARS form; every task cites requirements; every property
validates requirements; waves pass the checker; checkpoints name commands and
pass criteria; no task re-implements shipped work; amendments and remediation
banners present where they apply.

## 6. Starting a new project from the second brain

1. Scaffold the project record: `research/`, `business/`, `<specs>/steering/`,
   `<specs>/MASTER_SEQUENCING.md`, `.claude/state/`, a fact registry and
   a decision-record folder.
2. Write steering from the research, with evidence notes.
3. Inventory what exists (code, prototypes, tests) at a commit.
4. Author requirements-first; design; tasks with waves; refine and validate.
5. Sequence by dependency; name the validation milestone and its gates.
6. Run the feature lifecycle per spec; keep the state files and the audit
   tables current; reconcile periodically.
