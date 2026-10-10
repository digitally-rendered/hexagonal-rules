# Plugin ensembles, pipelines, and LLM adapters (Python)

Source: a pipeline application. The abstract lifecycle and harness are in
`shared/09-ingestion-lifecycle.md`, `shared/10-ai-harness.md` and
`shared/11-operating-skills.md`; this file is the Python idiom. Level 1 of
the ladder: a hand-written hexagon whose
variable behaviour is plugins, whose long work is a cached pipeline, and whose
output is vetted by an independent judge layer
(`shared/06-evals-and-verification.md`).

## 1. Layer map

| Layer | Location | Contents |
|---|---|---|
| Domain | `core/document.py`, `core/plugin.py`, `core/context.py`, `core/config.py`, `core/vocab.py` | `Document`, `Field`, `ExtractionResult`, plugin base hierarchy, `ExtractionContext` (pure DTO), config, closed vocabularies |
| Ports | `domain/ports.py` | primary: `DocumentParserPort`, `ConflictResolverPort`; secondary: `DocumentReaderPort`, `PluginRepositoryPort`, `CachePort`, `LLMPort`, `StoragePort`, `MetricsPort`, `ConfigurationPort`, `ExportPort`, `<Artifact>SchemaPort`, `PrefillPort` |
| Services | `domain/services.py` | `DocumentParsingService`, `ConflictResolutionService`, `FieldEnrichmentService`; orchestration via injected ports |
| Adapters | `adapters/` | readers (filesystem, S3, HTTP), plugin repository, LLM adapters (local model server, hosted provider CLI, local inference runtime), prompt layout/versions, schema storage |
| Plugins | `plugins/{extraction,detection,validation,enrichment}/` | concrete strategies |
| Composition root | `core/parser.py` (`<Entity>Parser`), CLI | wires ports to adapters; creating default adapters here is allowed |
| Pipeline | `pipeline/` | build drivers, stage cache, run store, provenance, gate records, miss log |
| Validation | `validation/` | orchestrator, judges, rubric, findings, source index |

Hard violations: domain importing adapters or external libraries; a port that
is not abstract; a service instantiating an adapter; business logic in an
adapter; circular layer dependencies. Soft: domain doing I/O; adapters mixing
concerns; a new external dependency without a port; a service with too many
ports. `ExtractionContext` carrying pre-loaded bytes is data, not I/O.

## 2. The plugin contract

```python
class MyExtractor(ExtractionPlugin):
    name = "MyExtractor"; version = "1.0.0"
    def get_capabilities(self) -> list[PluginCapability]: ...
    def get_priority(self) -> PluginPriority: ...        # CRITICAL..BACKGROUND
    def can_process(self, context: ExtractionContext) -> bool: ...
    def extract(self, context: ExtractionContext) -> list[Field]: ...
```

- Base classes per stage: `ExtractionPlugin` → `DetectionPlugin` →
  `ValidationPlugin` → `EnrichmentPlugin`; each stage sees the accumulated
  output of the previous (`context.text_content`, `context.existing_fields`).
- **Lazy-import external libraries inside `can_process`**, never at module
  top; a missing dependency makes the plugin report unavailable, not crash the
  import. The package `__init__` wraps each plugin import in `try/except
  ImportError`.
- `can_process` is called **once**, by the service; `process()` does not
  re-check. Keep it cheap; ML model probing happens once.
- Every emitted `Field` sets `source_plugin=self.name`, a meaningful
  `confidence` in `[0,1]`, `field_type`, and `metadata["extraction_method"]`.
- Errors are logged and the plugin returns an empty result; it never raises
  into the service.
- Binary document types are never decoded as text; detectors read
  `text_content` produced by extractors.
- Patterns are pre-compiled at module level; new locale or region patterns are
  added, never substituted for existing ones; bump `version` on significant
  change.
- Per-plugin timeouts are enforced by the service; one hung plugin must not
  stall the parse.

## 3. Provenance

- `Field.emit / enhanced_from / merge_from` are the only factories; each
  records a `producer_chain` step (`emit`, `enhance`, `merge`, `override`)
  with plugin, value, confidence, timestamp.
- Validation and enrichment **record a step on every touch** even when the
  value does not change.
- Conflict resolution (consensus → highest confidence → LLM) records an
  `override` step and keeps the losing candidates in metadata.
- `to_dict()` serializes the chain, `validation_status`, and
  `extraction_method`. A readiness report lists which plugins ran and which
  were blocked on a missing dependency; evaluation output consumes it.
- Downstream consumers prefer converged fields; discarding `converged_*`
  because they "inflate counts" throws away the ensemble.

## 4. Services and ports

- Services take ports in the constructor and never construct adapters.
- The `LLMPort` is a wide ABC of named operations (`extract_<entity>`,
  `classify_<entity>`, `generate_<artifact>`, …), each documenting the
  context keys it requires and the keys it returns. Adapters implement all of
  them; prompts live with the adapter (`_llm_prompts*.py`), schemas in
  `_<provider>_schemas.py`.
- Prompt templates are versioned (`prompt_versions.py`) and listed in a
  manifest; the manifest is checked by pre-flight.
- Model tiers are one table (`model_tiers.py`: REASONING, VET_JUDGE, …); the
  adapter reads its default from it.

## 5. Pipeline stages

- Every stage: typed input, typed output, preconditions, gate command. Stages
  are independently re-runnable from their inputs.
- A `BuildPlan` describes every invocation: scope axes (regions,
  domains, categories, stage range, freshness), resolved scope, and
  outputs. Full rebuild is the degenerate plan.
- Stage cache key per stage (`compute_stage_key(stage, inputs)`): e.g.
  `extract_<entity> = chunk_text_hash + prompt_hash + schema_hash +
  model_hash`; a dependent extraction stage adds the digest of the upstream
  entity **content** it consumed. Sampler options that do not change
  semantics are not in the key.
- A per-package run store (SQLite) records runs, stage runs (`success`, `success-cached`,
  `fail`, `running`), LLM calls, misses, gate records. Stranded `running` rows
  after a kill are cosmetic.
- Deterministic post-passes (enum corrections, source-text attachment,
  identity stamping, residual passes) run inside the build after the LLM
  stage; they record provenance and never re-key extraction.
- Label-only changes (classification, grammar) are post-extraction and must
  never re-key extraction; pre-flight blocks a changed extraction prompt
  unless explicitly accepted with a reason.
- Concurrency rules are stated once and obeyed by drivers (one GPU build at a
  time; a network vet may run beside a GPU build; CPU stages beside either).

## 6. LLM adapters

- Structured output uses schema-constrained generation; Pydantic validation is
  the second line.
- A truncated response is more often a greedy repetition loop than an over-long
  chunk: retry once with a repetition penalty before shrinking chunks or
  raising caps.
- Silent fallbacks (`{}` on unparsable JSON) are forbidden; a parse failure is
  a recorded miss with the raw response kept.
- Rate-limit and auth-death errors are typed (`<Provider>RateLimitError`) so the
  orchestrator can distinguish "wait and resume" from "abort as systemic".
- Spend is tracked in the run summary and logged at thresholds; enforcement is
  opt-in for metered users.
- Multi-host support via environment (`<APP>_LLM_HOST`); the model
  hash in the cache key keeps dev-tier output out of production caches.

## 7. Identity

- Addresses/URNs are minted, compared and resolved by one function each
  (`canonical/urn.py`); a guard test fails the suite on a local
  re-implementation.
- Canonical ids are UUID5 of the canonical citation; `short_id` is a
  deterministic human alias. The LLM never invents ids.
- Identity resolution is a gate that must pass before any stage that joins on
  identity.

## 8. Review agents and skills

- `hex-arch-reviewer`: classifies each file by layer, reports hard/soft
  violations with lines.
- `plugin-developer` / `plugin-fixer` / `detection-evaluator`: scaffold, fix,
  and evaluate plugins against fixture corpora; always add patterns, measure
  before/after coverage, run the suite after every change.
- `pack-quality-auditor`, `binding-contract-auditor`: read-only audits with a
  fixed report shape, quoting the contract and literal violations.
- Skills are read-only inspection tools (`plugin-review`'s `inspect_parse.py`
  shows stage order, readiness, per-plugin contribution, and a field's chain).
