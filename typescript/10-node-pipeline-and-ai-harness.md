# Plugin pipeline, ingestion lifecycle, and AI harness (TypeScript / Node)

The Level 1 rung in TypeScript: the plugin ensemble, the staged ingestion
lifecycle (`shared/09`), the AI harness (`shared/10`) and the operating
skills (`shared/11`). Mirrors `python/03-plugin-pipeline.md`. Stack assumed:
Node ≥ 20 (worker threads or a job queue for parallelism), TypeScript strict,
Zod + Ajv, `better-sqlite3` for the run store, Pino, Vitest, an
OpenAI-compatible HTTP client for model servers, the provider SDK or a CLI
wrapper for judges.

## 1. Layer map

| Layer | Location | Contents |
|---|---|---|
| Domain | `core/document.ts`, `core/plugin.ts`, `core/context.ts`, `core/config.ts`, `core/vocab.ts` | `Document`, `Field`, `ExtractionResult`, plugin base types, `ExtractionContext` (pure data), config, closed vocabularies |
| Ports | `domain/ports.ts` | `DocumentReaderPort`, `PluginRepositoryPort`, `CachePort`, `LLMPort`, `StoragePort`, `MetricsPort`, `ExportPort`, … |
| Services | `domain/services/` | `DocumentParsingService`, `ConflictResolutionService`, `FieldEnrichmentService` |
| Adapters | `adapters/` | readers (fs, S3, HTTP), plugin repository, LLM adapters (local server, hosted API, CLI judge), prompt layout and manifest, schema storage |
| Plugins | `plugins/{extraction,detection,validation,enrichment}/` | strategies |
| Composition root | `core/parser.ts` (`UniversalParser`), CLI | wires ports to adapters |
| Pipeline | `pipeline/` | build drivers, stage cache, run store, provenance, gate records, miss log |
| Validation | `validation/` | orchestrator, judges, rubric, findings, source index |

Hard and soft violations are the shared ones; enforce with
`eslint-plugin-boundaries` and `dependency-cruiser`.

## 2. The plugin contract

```ts
export abstract class ExtractionPlugin implements Plugin {
  readonly name = this.constructor.name; readonly version = '1.0.0';
  abstract capabilities(): PluginCapability[];
  abstract priority(): PluginPriority;
  abstract canProcess(ctx: ExtractionContext): Promise<boolean>;
  abstract extract(ctx: ExtractionContext): Promise<Field[]>;
}
```

- Stage bases: extraction → detection → validation → enrichment; each sees
  the accumulated output of the previous.
- **Lazy-load optional dependencies inside `canProcess`** with a guarded
  dynamic `import()`; a missing package makes the plugin unavailable, not
  the process broken. The plugin index registers each plugin behind a
  try/catch on import.
- `canProcess` is called once by the service; keep it cheap.
- Every emitted `Field` sets `sourcePlugin`, a meaningful `confidence`,
  `fieldType`, and `metadata.extractionMethod`; errors are logged and
  yield an empty result.
- The service enforces a per-plugin timeout with `AbortSignal.timeout()` and
  runs plugins in priority order; heavy plugins run in worker threads or a
  queue so one cannot stall the loop.
- Patterns are compiled once at module scope; add, never substitute.

## 3. Provenance

- `Field.emit / enhancedFrom / mergeFrom` are the only factories and each
  records a `producerChain` step (`emit | enhance | merge | override`) with
  plugin, value, confidence and timestamp. Validation and enrichment record a
  step on every touch. Conflict resolution records `override` and keeps the
  losers. `toJSON()` preserves the chain and every status field.
- A readiness report lists plugins that ran and plugins blocked on a
  dependency; evaluation output consumes it.

## 4. Ingestion lifecycle (Node idiom)

- Stages are modules exporting `run(plan, store): Promise<StageOutput>` with
  typed input/output (Zod schemas) and a `gate(): Promise<GateRecord>`.
- The build plan is a Zod-validated object logged with the run.
- Stage cache key: `sha256(JSON.stringify({stage, inputs}, sortedReplacer))`
  with large blobs pre-hashed; the run store is SQLite (`better-sqlite3`)
  with tables for runs, stage runs, stage outputs, LLM calls, misses,
  reviews, gate records; migrations applied on open.
- Chain scripts are TypeScript entrypoints (`tsx scripts/cycle.ts`) that
  stop on the first failing gate; never ad-hoc `&&` lines.
- Concurrency: one GPU/LLM-server job at a time via a lock file or a
  single-concurrency queue; CPU stages may run alongside.
- Miss log: an append-only JSONL writer with registered kinds; a test sweeps
  the source for unregistered kind literals.

## 5. AI harness (Node idiom)

- `LLMPort` is an interface of named operations; adapters: a local model
  server over its HTTP API, a hosted provider SDK, a CLI judge spawned with
  `child_process` and a JSON output contract.
- Model tiers in one module with precedence argument > env > default.
- Prompt templates are exported string constants; `config/prompt-manifest.yaml`
  pins `name → version, sha256`; a Vitest test fails on drift.
- Structured output: pass the JSON Schema to the server's constrained
  decoding option; validate the result with Ajv or Zod as the second line;
  wrap arrays in an object schema.
- Assert prompt size against the model's context before calling; typed
  errors `PromptTooLargeError`, `ResponseParseError`, `RateLimitError`,
  `SystemicFailureError`.
- Truncation: retry once with a repetition penalty; then raise.
- Provenance per call: model descriptor with digest (from the server's
  model listing), prompt hash, schema hash, sampler identity, latency,
  attempts, usage and cost (`null` with reason when unknown).
- Judge adapter: static-first prompt (rubric as system, item as head),
  output-shape validation, rubric-conformance check before caching, bounded
  retry with backoff, systemic-death markers, cost accounting.

## 6. Identity

One module mints, compares and resolves addresses/URNs; an ESLint rule or
AST test (ts-morph) fails on a second normaliser.

## 7. Tests

- Vitest; fixtures are fictional; golden chunks per source kind with
  snapshot tests per prompt × chunk.
- Contract tests for every port implementation; a fake `LLMPort` drives the
  pipeline end to end.
- Property tests (`fast-check`) for the provenance chain and the cache key.
- Integration tests for the run store on a temp SQLite file.
