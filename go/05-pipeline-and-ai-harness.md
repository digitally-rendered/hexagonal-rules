# Plugin pipeline, ingestion lifecycle, and AI harness (Go)

The Level 1 rung in Go: the plugin ensemble, the staged ingestion lifecycle
(`shared/09`), the AI harness (`shared/10`) and the operating skills
(`shared/11`). Mirrors `python/03-plugin-pipeline.md`. Stack assumed:
Go ≥ 1.22, `errgroup`/worker pools, `modernc.org/sqlite` or `mattn/go-sqlite3`
for the run store, `santhosh-tekuri/jsonschema` for validation, `log/slog`,
Cobra for drivers, an OpenAI-compatible HTTP client for model servers,
`os/exec` for CLI judges.

## 1. Package map

```
pkg/core/
  document/   Document, Field, ExtractionResult, producer chain
  plugin/     Plugin interface, capability and priority enums, stage bases
  context/    ExtractionContext (pure data)
  vocab/      closed vocabularies (one authority)
  port/       DocumentReader, PluginRepository, Cache, Assistant (LLM), Storage, Metrics, Export, Judge
  service/    ParsingService, ConflictResolution, Enrichment
pkg/adapter/driven/
  reader/{fs,s3,http}/  pluginrepo/  llm/{local,hosted,cli}/  prompt/  storage/
pkg/plugin/{extraction,detection,validation,enrichment}/
pkg/pipeline/   build plan, stage cache, run store, provenance, gate records, miss log, drivers
pkg/validation/ orchestrator, judges, rubric, findings, source index
cmd/<tool>/     Cobra commands: parse, build, vet, audit, progress, cycle
```

`pkg/core/**` never imports `pkg/adapter/**` or `pkg/plugin/**`; plugins
import core; the composition root (`pkg/engine` or `cmd`) imports all.

## 2. The plugin contract

```go
type Plugin interface {
    Name() string
    Version() string
    Capabilities() []Capability
    Priority() Priority
    CanProcess(ctx context.Context, ec *ExtractionContext) bool
    Extract(ctx context.Context, ec *ExtractionContext) ([]Field, error)
}
```

- Stage bases are embedded structs providing default capabilities and
  priority; plugins override `CanProcess` and `Extract`.
- Optional dependencies: a plugin that needs an external binary or model
  checks availability in `CanProcess` (`exec.LookPath`, a cached probe) and
  reports unavailable rather than failing; Go has no lazy import, so
  optional heavy dependencies live behind build tags (`//go:build ocr`) and
  the plugin registry includes them only when built.
- Registration: a `pluginrepo` that returns plugins in priority order; each
  plugin registers in its package `init()` behind the build tag.
- Every `Field` carries `SourcePlugin`, a meaningful `Confidence`,
  `FieldType`, `Metadata["extraction_method"]`; errors are returned (not
  panicked) and the service logs them and continues.
- The service runs plugins with `context.WithTimeout` per plugin and a
  bounded worker pool; a hung plugin is cancelled, not waited on.

## 3. Provenance

- `field.Emit / EnhancedFrom / MergeFrom` are the only constructors; each
  appends a `ProducerStep{Plugin, Action, Value, Confidence, At}`.
  Validation and enrichment append on every touch; conflict resolution
  appends `override` and keeps losers in metadata. JSON marshalling keeps
  the chain and every status field.
- A readiness report enumerates ran versus blocked plugins.

## 4. Ingestion lifecycle (Go idiom)

- Each stage is a package exposing `Run(ctx, plan Plan, store *RunStore)
  (Output, error)` and `Gate(ctx, subject) (GateRecord, error)`; inputs and
  outputs are structs validated on construction.
- `Plan` is a struct with scope axes, stage range, freshness, output mode;
  serialised with the run.
- Stage key: `sha256` over canonical JSON (sorted keys, `ensure_ascii`
  equivalent) of `{stage, inputs}` with large blobs pre-hashed.
- Run store: SQLite with runs, stage runs, stage outputs, LLM calls, misses,
  reviews, gate records; migrations applied on open; writes in transactions.
- Chain drivers are Cobra commands that stop on the first failing gate and
  never accept a bypass flag inside a chain.
- Concurrency: a file lock or single-slot semaphore for GPU/LLM-server
  stages; CPU stages may run under `errgroup` with a limit.
- Miss log: append-only JSONL with a registered kind enum; a test parses the
  source (`go/ast`) for `misslog.Append(` calls and asserts the kind exists.

## 5. AI harness (Go idiom)

- `port.Assistant` is an interface of named operations
  (`ExtractEntities`, `Classify`, `Generate`, `ReviewArtifact`); adapters in
  `adapter/driven/llm/{local,hosted,cli}`.
- Model tiers: one table `map[Tier]string` with precedence option > env >
  default, resolved at adapter construction.
- Prompts are string constants; `config/prompt_manifest.yaml` pins
  `name → version, sha256`; a test fails on drift (prompts enumerated via a
  registry map, since Go cannot reflect over package constants).
- Static-first prompt layout; never re-lay-out a prompt whose hash keys a
  cache.
- Structured output: send the JSON Schema with the request's structured
  output option; validate with `jsonschema`; wrap arrays; assert the prompt
  fits the context window first.
- Typed errors: `ErrPromptTooLarge`, `ParseError`, `RateLimitError`,
  `SystemicFailure`; truncation retried once with a repetition penalty.
- Provenance per call: `ModelDescriptor{Adapter, Model, Digest}` (digests
  from the server's model list), prompt hash, schema hash, sampler identity,
  latency, attempts, usage/cost with an availability reason when unknown.
- Judge adapter: rubric as system block, item as head, shape validation,
  rubric conformance before caching, bounded backoff, death markers, cost
  totals.

## 6. Identity

One package mints, compares and resolves addresses; an `go/ast` test fails
on a second normaliser.

## 7. Tests

- Table-driven with testify; fixtures fictional; golden chunks per source
  kind with golden-file tests per prompt × chunk (`-update` flag).
- Contract tests over every port implementation; a fake `Assistant` drives
  the pipeline end to end.
- Property-style tests (`testing/quick` or `rapid`) for the producer chain
  and cache key.
- Run store integration tests on a temp SQLite file; `-race` always.
