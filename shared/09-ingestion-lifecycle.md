# The data ingestion lifecycle

An ingestion system turns an external corpus into versioned, reproducible,
citable packages that applications and agents consume. This is the abstract
lifecycle behind the pipeline application: a durable **format**, a
replaceable **producer**, a **consumer toolkit**, and a **registry**. It
pairs with `shared/10-ai-harness.md` (how the LLM work inside it is done)
and `shared/06-evals-and-verification.md` (how its output is vetted).

## 1. Four layers, one durable artifact

```
Layer 4  Registry / distribution     immutable, content-addressed packages
Layer 3  Consumption toolkit         load / resolve / query / simulate / commit; same verbs for humans and agents
Layer 2  Producer(s)                 this pipeline; human curation; external producers
Layer 1  Format spec                 THE artifact: schemas, identity, versioning, provenance, verbs
```

- **Format before code.** The format is the durable artifact; producer and
  consumer are replaceable. When producer and format disagree, the format
  wins and the producer is fixed. Schemas are target contracts: a real case
  the schema cannot express is a proposed format delta, never a downstream
  workaround.
- A producer's intermediate store is an implementation detail; the
  published package is the output.
- **Multi-producer by design.** `producer ∈ {pipeline, human, external:<name>}`
  on every entity; merge rules keep them from stomping each other (§9).
- **Dual audience.** The same read, reasoning and control surface serves a
  person (UI) and an agent (tool server), under one authority model (§11).

## 2. Stages

```
0 acquire      download + hash-pin raw bytes; one source record per fetch
1 preprocess   normalise, segment by natural unit, resolve internal references, build an offset index
2 extract      LLM-driven, schema-enforced; upstream tier first; deterministic ids; per-call audit
3 resolve      dedup by stable id; cross-link to reference trees; detect override deltas
4 enrich       derive structures (workflow graphs, question sets, field maps); structurally validated
5 cascade      materialise the override stack into flat effective sets per scope
6 embed        optional vectors per entity type, model-pinned
7 package      content hashes, delta classification, version + compat, manifest, changelog, proposals
8 publish      to a registry that never deletes and verifies by hash
```

This is the abstract lifecycle, not a product's stage list: every
ingestion system acquires, preprocesses, extracts, resolves, enriches,
cascades, packages and publishes, and the names above are the vocabulary
the other files cite. A product's sub-stages (which structures it derives,
which trees it links) live in its own documentation and are not restated
here.

Every stage has a **typed input, a typed output, preconditions, and a gate
command**. Stages are independently re-runnable from their inputs; rebuilding
stage N does not rerun 0..N-1 when their outputs are unchanged. Hashes drive
cache invalidation.

## 3. Scope, freshness, and the build plan

Every invocation, full or incremental, is described by a **build plan**
logged with the build so any rebuild can be replayed exactly:

| Axis | Examples | Default |
|---|---|---|
| region / tenant | `A`, `A-SUB`, `A-*` | all |
| domain | `domain-a`, `domain-b` | all in scope |
| category | `category-a`, `category-b` | all |
| stage range | `from=2,to=5`, `from=5` | stale-driven |
| freshness | `--only-stale` (default), `--force`, `--since <date>` | only stale |
| output | `package` (whole scope) or `proposal` (partial scope) | by scope |

- A scope filter on one axis **propagates** to every downstream stage.
- **Upstream-first discipline**: a dependent-scope build is rejected if its
  upstream tier is stale; the planner auto-expands or aborts with a clear
  error. A failed upstream build blocks downstream extraction; there is no
  best-effort re-extraction of upstream content inside a downstream pass.
- **Incremental cache**: each stage emits `(input_hash, output_hash)` per
  entity; a re-run skips matching inputs. Invalidation is **transitive**
  along the dependency graph; users never remember what depends on what.
- **Surgical rebuild** of one entity computes its dependency closure, runs
  only that, and emits a proposal by default.
- The scraper has no privileged code path: it is `build --from-stage 0
  --emit proposal --only-stale`. Scheduled scraping produces proposals, never
  commits.

## 4. Acquisition and preprocessing

- Source record per fetch, even on cache hit: deterministic `source_id`,
  URL, kind, region, fetched-at, fetcher, raw-bytes `content_hash`, path,
  ETag/Last-Modified. Hash-pinning raw bytes is the foundation of
  reproducibility; when two builds disagree, compare input hashes first.
- Re-fetch when headers indicate change, but **never overwrite**: rename the
  prior file with its hash suffix and keep the chain.
- **Natural text boundaries.** Every chunk handed to a model aligns with
  the source's logical units; the model never sees a partial unit. Boundary
  preference: logical section → paragraph → line → never raw characters. A
  new source kind gets its own splitter mode; the character fallback exists
  only to keep unknown formats degraded, not broken.
- Preserve citations and anchors while stripping chrome; rewrite internal
  references to structured tuples before extraction.
- The offset index holds offsets, not text; read source text through one
  accessor.
- Chunk density, not size, drives truncation; keep related sub-units atomic
  (group by root) and measure chunks before building.

## 5. Extraction

- **Schema-enforced output**: sampler-level JSON-schema constraint first,
  model validation second; regex recovery of model output is forbidden.
- Sampling for reproducible builds: temperature 0, fixed seed recorded in
  the manifest, single shot per unit (resampling masks regressions; flag and
  halt).
- **Kind-aware prompts** selected by document kind, each with its own
  template hash so a new kind invalidates only its own cache.
- **Post-model canonicalisation**: mechanically derived addresses replace
  whatever the model emitted before persistence; the model never invents
  identifiers.
- **Per-call audit** (source, unit, prompt hash, model hash, output hash,
  latency) to a producer-internal log.
- **Miss log**: every site where input is dropped, renamed, or
  fallback-substituted appends a typed record (`kind`, subject, unit,
  structured `details` with near-matches); kinds are registered and a test
  sweeps for unregistered literals. Without it, silent quality regressions
  surface only downstream.
- Deterministic post-passes (enum corrections, source-text attachment,
  identity stamping, residual passes for uncovered units) run inside the
  build and never re-key extraction.

## 6. Resolution, enrichment, cascade

- Stable identity is deterministic (UUID5 of the canonical citation, or a
  URN); a human alias (`short_id`) is derived from the same inputs.
  Identity is minted, compared and resolved by one function each.
- Cross-links between reference trees are a one-shot curated tool, not a
  recurring stage; the pipeline consults them and does not regenerate them.
- Overrides are **deltas** (`extends | replaces | restricts` + changed
  fields) pointing at a parent, never cloned copies.
- Derived structures are validated structurally before acceptance
  (connected, acyclic, every reference resolves); a violation aborts with
  the exact invariant, never best-effort output.
- The producer **materialises** the override stack into flat effective sets
  per scope with a trace of contributing ids; consumers read the flat set and
  never re-walk the cascade.

## 7. Packaging and versioning

- Per-entity `content_hash` over normalised JSON with envelope metadata
  excluded; entities carry `content_hash` and `last_modified`, no per-entity
  version number.
- **Calendar version + compatibility channel**: `YYYY.MM.PATCH` for humans,
  `compat: v<int>` for binding safety. `compat` bumps only on breaking change
  (semantics that flip existing decisions, removals, topology changes,
  renames); additions and wording do not bump it. Auto-commit is only ever
  allowed when `compat` is unchanged.
- The manifest records format version, package id, version, compat, trust
  tier, dependencies as ranges (`compat` + date bounds), the build (pipeline
  version, model hashes, prompt hashes, deterministic flag), counts,
  entity hashes, and **derived artifacts** hashed over bytes with
  `{kind, path, content_hash, count}`.
- **One version pins the whole consumable surface**: assembly fails on a
  declared artifact whose pack copy differs from its source (freshness) or
  whose provenance names inputs the bundle does not ship (coherence).
- Dependencies exist for one purpose: deduplicating shared upstream content.
  Source files live once in the upstream package and are referenced by id;
  materialised outputs inline them for consumer simplicity.
- A changelog is generated from the structured delta; a format validator runs
  on every package; a `pipeline/` record captures the full build trace.

## 8. Provenance, trust, reproducibility

Every entity carries `provenance`: producer and version, extracted-at,
source document id and hash, model descriptor with digest, prompt hash,
input citation, producer-reported confidence (a signal, not a measure),
review status, reviewer, reviewed-at.

| Trust tier | Meaning | Consumer behaviour |
|---|---|---|
| `seed` | unsigned, unverified | warn; explicit opt-in to load |
| `signed` | producer-signed | verify before load |
| `certified` | counter-signed by an authority | reserved |

A package is reproducible when the same corpus, pipeline version and model
pins yield byte-identical output (excluding `built_at`). The producer
guarantees it by hash-pinned inputs, pinned models and prompts, deterministic
sampling, hashed stage inputs, sorted output order, and a CI gate that builds
twice and diffs.

## 9. Proposals and multi-actor merge

- Any change from any actor is an append-only **proposal**: from/to version
  and compat, actor and actor type, reason, source diff, entity delta,
  `requires_compat_bump` (computed), status, auto-commit eligibility, review
  fields.
- Auto-commit policy: pipeline-authored, same-compat, non-materially-
  affecting proposals may graduate to auto-commit once the pipeline is
  proven; until then every proposal is pending. Human-authored and
  compat-bumping proposals always await review.
- Merge rules on rebuild: an entity another actor produced is untouched; a
  pipeline entity marked approved by review is pinned and drift becomes a
  proposal; everything else rebuilds normally.

## 10. Consumption: lockfiles, states, verbs

- Consumers pin `(package, version, compat, content_hash)` tuples in a
  lockfile; the hash guarantees reproducibility, the version is for humans,
  compat is the binding safety signal. Loading verifies hashes and refuses on
  mismatch; dependencies resolve transitively.
- Consumer records are **open** (auto-migrate on same-compat bumps, human
  review on compat bumps), **pinned** (frozen by a practitioner, with reason
  and optional expiry), or **closed** (frozen forever by a closure lockfile
  hash). Reopening chooses explicitly between original and current rules and
  never erases the closure.
- Registries never delete, keep versions monotonic, treat hash mismatch as
  an integrity error, and may yank but not remove.
- **Verb contracts**: every reading verb has a `why_*`/`explain_*` sibling
  returning structured rationale; every mutating verb has a `simulate_`
  sibling and writes an audit record `(actor, actor_type, reason, timestamp,
  input_hash)`; every rationale that makes a domain claim carries at least
  one source citation; rendered documents and forms carry per-section and
  per-field provenance, and anything AI-drafted cannot be committed to the
  record unreviewed.
  A conformance self-test exercises each rule; a verb without its siblings
  fails it.
- Hot reload is lazy by default; eager mode needs a registered migration
  handler; pinned mode is required for long-running deterministic work.

## 11. Authority and the agent loop

| Capability | Held by | Gates |
|---|---|---|
| `read`, `propose` | any authenticated actor | reading, proposing, simulating |
| `commit:<record>` | actors with record access | mutating verbs scoped to a record |
| `commit:proposal`, `review:ai_draft`, `migrate:compat` | humans | committing proposals, approving drafts, compat migrations |
| `lifecycle:close`, `file:bundle` | actors with those rights | closure, filing |

Capabilities are enforced by the toolkit, not the consuming app; the app
maps its auth model to capabilities at the verb boundary. Every tool-server
call runs as `actor_type: ai`; the expected loop is read → reason → propose
or simulate → hand off → a human commits. Every agent call is audited with
model identity, verb, inputs, outputs and session.

## 12. Process controls

Each of these was a lapse first; each is now enforced by a script or test,
not a convention:

- A multi-step run is a **committed chain script**; any gate failure stops
  it; downstream stages check "upstream done and every gate PASS".
- Pre-flight (full test suite, prompt manifest in sync, no uncommitted
  cache-keyed code, nothing else running) runs before any build, rebuild or
  vet and is never run with a bypass flag inside a chain.
- Derived stages and assembly run **before** the gates, so a gate stop never
  leaves a half-assembled package.
- A corpus swap happens only after a proof that every cited unit survives,
  inside the rebuild step.
- Every gate writes a **gate record** (stage, subject, verdict, metrics,
  inputs hash); the progress reporter reads records and marks stale ones,
  never recomputes.
- An extraction-prompt change is flagged before the build; label-only
  changes go through the classification stage so they never re-key
  extraction.
- A change to identity handling is proven by simulation (0 lost, 0 changed)
  before it lands; a source-dependent classifier change is simulated over
  every package.
- Concurrency rules are stated once (which stages contend for GPU, network,
  CPU) and obeyed by the drivers.
- Read the manifest, not the folders: a package never assembled ships
  nothing, however healthy its directories look.
