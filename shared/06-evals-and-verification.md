# Evaluations and verification of generated output

Distilled from a pipeline application's review framework (plugin
ensembles, the vet/judge layer, end-to-end audits) and the enforcement
learnings of a schema-driven application. Applies to any system whose output is produced by an LLM, an
ensemble of extractors, or any generator that reports its own quality.

## 1. Self-reported quality signals never gate

A signal the generator reports about its own output cannot gate that output.
Measured three ways: embedding similarity did not predict judge verdicts;
LLM classification confidence was uniformly 0.85–1.00 **including on clear
errors**; a model producing 100% valid JSON said nothing about faithfulness.

**Rule:** every generated quality claim needs an independent validator: a
judge, a deterministic cross-check, or a second modality. The cheap
self-report is at best a router for prioritisation, never a gate.

## 2. Gates are commands with exit codes

- A gate is a script that exits non-zero, never a judgement call.
- Mechanical work (source resolution, citation format, address structure,
  chunk boundaries, referential integrity, counts) is deterministic and runs
  as a gate. The LLM judges substance only: "does this text support this
  claim?"
- Every stage has a typed input, a typed output, preconditions, and a gate
  that must pass before the next stage reads its output. Stages must not
  silently consume stale upstream artifacts; record what version was joined
  against (a **freshness contract**).
- Identity resolution gates before everything that joins on identity.

## 3. Provenance survives every touch

- Each contribution to an artifact records a step: who (plugin/model/judge),
  what action (`emit` / `enhance` / `merge` / `override`), the value and
  confidence at that step, and a timestamp.
- Serialization MUST preserve the chain and every status field; a `to_dict`
  that drops `validation_status` makes validation invisible.
- Conflict resolution records the losing candidates and an `override` step;
  replacing the winner silently erases the signal the ensemble exists to
  produce.
- A plugin that stamps constant confidence is contributing noise; confidence
  tracks actual certainty (pattern strength, OCR probability, match score).
- Redundancy is a bug only when two sources cannot disagree in interesting
  ways (two PDF text engines on identical input). Their agreement earns no
  bonus.

## 4. Judges

- The judge receives a **rubric** of named checks. A review missing any
  canonical check name is non-conformant and is never cached; it is the
  signature of a judge that never saw the rubric.
- The canonical check names are parsed from the prompt text itself so they
  cannot drift from what the judge is sent.
- Judge identity is one table (`model_hash prefix → name`); an unknown judge
  reports as `other` rather than raising. Add a judge there, nowhere else.
- Prompts are split into a cacheable system rubric and a per-item head;
  `prompt_hash` covers the template, `rubric_hash` covers everything else the
  judge is told. Both are in the review's cache key.
- A check that could not be judged because the source was missing is
  `unverifiable`, not `fail`, and is excluded from pass-rate denominators.
- Three-judge adjudication for disputed items; model selection is validated on
  accuracy plus judges, never on speed or the model's self-justification.

## 5. Findings

One finding per `(artifact, check)`:

```
run_id, goal, layer, check, artifact_id, artifact_label,
verdict ∈ {pass, warn, fail, unverifiable}, score 0..1,
source_quote (verbatim), explanation (one sentence),
suggested_correction, producer_layer_to_fix, rerun_command
```

Each finding maps to a UI row and to a producer fix command. The
`layer → producer stage` table is one source of truth.

## 6. Run status is honest

- A layer that judges fewer than a coverage floor (95%) of its steps makes the
  run `partial`, which audits treat as failure. "Success" with 22.5%
  coverage was the incident.
- The same error N times in a row, or a known systemic marker ("Not logged
  in"), aborts the run as a systemic failure instead of grinding out
  thousands of identical failures.
- Verdicts persist as they land; a killed run resumes from the cache.
- Spend is tracked and logged, never enforced by default; the provider's limit
  is the limit and the loop polls to resume.

## 7. Content-addressed stage cache

- `stage_key = sha256(canonical_json({stage, inputs}))`.
- **Everything that affects the output is in the inputs** (chunk hash, prompt
  hash, schema hash, model hash, upstream artifact digests). **Nothing that
  does not** (run id, timestamps, log level, sampler tuning that does not change
  semantics).
- Large blobs are pre-hashed; the key is over small descriptors.
- The cache spans runs of the same package; that is the resumability story.
- Consequence: changing a shared schema enum re-keys every stage that
  consumed it. Say so before doing it.

## 8. The dev loop for prompt and extractor changes

```
edit → unit tests (instant)
     → preview on one golden chunk per kind (minutes, dev tier)
     → A/B diff against the prior prompt (minutes)
     → mechanical eval: JSON validity, schema conformance, citations resolve,
       modality preserved, no invented sections (instant)
     → snapshot diff, explicitly accepted (instant)
     → smoke build: one chunk per source, end to end (minutes)
     → full build (hours) only when dialled in
```

- **Golden chunks** are small real slices of each source kind, checked in; a
  new failure pattern adds its chunk and a regression test pointing at it.
- Two model tiers: production (canonical, slow) and development (fast, never
  committed). Model hash is in the cache key, so dev output cannot pollute
  production.
- Committing a prompt change requires: tests green, preview reviewed on every
  kind the prompt covers, mechanical eval green, snapshots explicitly updated,
  smoke green if on the hot path, and the golden chunks named in the commit.
- No LLM-touching change ships without a sub-minute feedback loop in front of
  it.

## 9. Partial refactors are the top defect class

A policy that must hold at N sites holds at fewer than N; the correct version
already existed somewhere. Nothing fails; one site is quietly wrong.

- **Review question:** "Is this decision expressed anywhere else, and do those
  places agree?" If there is another shaper, gate, or caller, the change is not
  done.
- Use `ast` sweeps, not text search, to find sibling sites.
- Write a drift test comparing the siblings; validate it by re-introducing the
  defect and watching it fail.
- Retiring a contract from tests does not retire it from scripts; the script
  gates the build.

## 10. Count the population

A number must name the population it counted: the directory, the filter, the
denominator. "544 files under `forms/a` + `forms/b`, of which 442 are
excluded by `EXCLUDED_SETS`", not "544 forms". Print
all three beside every number. A prediction is not a finding; measure before
planning.

## 11. Review agents

A review agent reads, queries, and reports; it does not edit. Its report has a
fixed shape (verdict, yardstick, counts with ratios, run state, spot checks,
contract quotes, literal example violations, producer responsible, status:
new / regression / known). A missing artifact is a finding, not a blocker;
keep going and surface everything in one report.

## 12. Verification tiers for code changes

| Tier | When | What |
|---|---|---|
| 1 file-level | after every file change | lint + types on the changed file |
| 2 unit | after a logical unit | unit tests |
| 3 full suite | before handoff | full backend + frontend suites with coverage |
| 4 handoff | before marking done | coverage thresholds; new generated surface visible in the API docs; state files updated; no new skips |

CI runs Tiers 2–3 again as a safety net; it must never be the first place a
failure is caught. If a test passes locally and fails in CI, suspect the
environment first.
