# The AI harness

How model calls are made inside an ingestion or parsing system so that
output is schema-valid, reproducible, cacheable, auditable, cheap to
iterate on, and independently judged. Pairs with
`shared/09-ingestion-lifecycle.md` (where the calls sit), the Level 1
rung's plugin ensemble (`shared/05`) and
`shared/06-evals-and-verification.md` (judging).

## 1. One port, many backends

- The core defines one wide **LLM port** of named operations
  (`extract_<entity>`, `classify_<thing>`, `generate_<artifact>`,
  `review_artifact`, `resolve_conflict`), each documenting the context keys
  it requires and the keys it returns. Prompts and output schemas live with
  the adapter, never in the core.
- Every backend is an adapter of that port: a local model server, a hosted
  API, a CLI-driven judge, an alternative runtime for the same weights.
  Swapping providers is one file. Backends carrying the same weights are kept
  on the same model so a quality delta has one candidate cause.
- Typed errors distinguish what the orchestrator should do: parse failure
  (record a miss, skip the item), prompt too large (shrink upstream, never
  truncate silently), rate limit (wait and resume), systemic death
  (abort the run).

## 2. Model tiers

- One table maps **jobs** to models: `reasoning` (long-context extraction),
  `classification` (cheap bulk), `field_labeling` (per-row, latency-bound,
  separate so it can stay small), `vet_judge` (grades everything else),
  `embedding`. Precedence is explicit argument > environment variable >
  default. Nothing else names a model id.
- Two deployment tiers: **production** (canonical output, cache hashes
  derive from it) and **development** (fast, never committed). The model hash
  is in every cache key, so tiers never pollute each other.
- Model selection is validated on accuracy and independent judges, never on
  speed or the model's self-justification; a disagreement between tiers is
  the most useful signal and points at an under-specified prompt.

## 3. Prompts

- Prompt templates are module constants with a **version manifest**
  (`name → version, sha256`); a test fails when a live hash drifts from the
  manifest, forcing the version bump into the same commit as the edit and
  exposing a partial edit across sibling prompts.
- **Kind-aware dispatch**: one template per source kind with kind-specific
  examples; each template hashed separately so a new kind invalidates only
  its own cache.
- **Static-first layout** for prefix caching: instructions and rubric first,
  the per-item text last, so a local server reuses the KV prefix. Never
  re-lay-out a prompt whose hash keys an extraction cache.
- Judge prompts split into a cacheable system rubric and a per-item head;
  the canonical check names are parsed from the rubric text so they cannot
  drift from what the judge is sent.
- Prompts constrain identifiers: cite the qualified unit path given in the
  chunk header, never invent one; reuse an existing upstream id rather than
  producing a new entity.
- Prompt changes follow the dev loop (golden chunks, preview, A/B diff,
  mechanical eval, snapshot, smoke) before any full run.

## 4. Structured output

- The output schema is passed as a **sampler constraint** (JSON-schema
  mode); the schema is part of the cache key. Array results are wrapped in
  an object schema and unwrapped after.
- Validation against typed models is the second line; drift is flagged,
  never silently accepted. Enum vocabularies in schemas derive from the one
  authority module.
- Assert the prompt fits the context window before the call and raise a
  typed error otherwise; the adapter's text chunker is a fallback for
  oversized units, never the primary boundary.
- A truncated response is usually a greedy repetition loop: retry once with
  a repetition penalty before shrinking chunks or raising caps. A still-
  truncated chunk is genuinely over-long.
- No silent fallback (`{}`, `[]`) on unparsable output; the item is a
  recorded miss with the raw response kept.
- Deterministic sampling for reproducible builds: temperature 0, fixed seed,
  a `sampler_identity` recorded in provenance; semantics-neutral sampler
  options stay out of the cache key.

## 5. Caching and provenance

- Stage key = hash of canonical JSON over everything that affects the
  output: chunk text hash, prompt hash, schema hash, model descriptor hash,
  digests of consumed upstream artifacts. Nothing else.
- The model descriptor is `<adapter>:<model>@<digest>`; adapters enumerate
  loaded models and their digests so provenance names what actually ran
  (failure to enumerate is itself a recorded miss).
- Every call writes a provenance record: model descriptor, prompt hash,
  schema hash, sampler identity, latency, attempts, usage and cost when
  available (`null` plus an availability reason otherwise). A multi-call
  unit keeps every call, not the last.
- Spend is tracked per run and logged at thresholds; enforcement is opt-in.

## 6. Judges

- `review_artifact(artifact, source_excerpt, rubric)` returns a review with
  named checks, verdicts, scores, source quotes, explanations and suggested
  corrections; shape and **rubric conformance** are validated before caching.
- Judge identity is one table of model-hash prefixes; local judges register
  at run time; unknown judges report as `other`.
- Retries use bounded backoff; **the same error N times in a row or a known
  death marker aborts the run as systemic** instead of grinding out
  thousands of identical failures (this is the one statement of the rule;
  `shared/06` §6 cites it); coverage below a floor makes the run partial.
  Check: the `judge` row of §8 (a fake adapter returning the same error N
  times makes the run abort with a systemic status).
- Three-judge adjudication for disputes; embeddings or cheap heuristics only
  triage order, never pass or fail.

## 7. Parsing and consuming with models

- Document parsing is an **ensemble** of plugins with confidence and
  provenance (the Level 1 rung, `shared/05`); a per-row model labeler is a
  plugin with a short timeout on the small tier.
- Conflict resolution is consensus → highest confidence → model, and the
  model step is a port call that records an `override` step.
- Consumption by agents goes through a read-only tool server exposing the
  same verbs as the library, under the capability gates; every call is
  audited with model identity. Agents read, reason with citations, propose
  or simulate, and hand off; humans commit.

## 8. Harness tests

Every rule above written as MUST or never is enforced by the row below
that names its concern; a rule with no row is SHOULD until it has one.

| Concern | Test |
|---|---|
| port conformance | every adapter satisfies the LLM port; a fake adapter drives the pipeline end to end |
| prompt manifest | live hash equals manifest hash per prompt |
| schema constraint | sample outputs validate; unknown enum values rejected |
| cache key | identical inputs → identical key; any input change → new key; sampler tuning → same key |
| truncation | a looping response is retried once with penalty; a genuinely long one raises |
| misses | every miss kind appended anywhere is registered |
| judge | non-conformant review is rejected and not cached; systemic failure aborts |
| golden chunks | snapshot per prompt × chunk; mechanical eval green |
