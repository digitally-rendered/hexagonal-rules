# Go rules

Read `shared/` first. Source: [stellar-drive](https://github.com/digitally-rendered/stellar-drive), the Go port of the
schema-driven framework (Level 4 of the ladder). The compiler and package
layout enforce what the Python rungs enforce with lint and AST tests.

| File | Contents |
|---|---|
| `01-go-hexagonal.md` | package levels, ports, decorators, container, function registry, events, errors, engine, codegen |
| `02-conventions.md` | interfaces, errors, context, options, naming, packages, middleware, concurrency, lint |
| `03-testing.md` | table-driven tests, build tags, `sdtest`, golden files, event capture |
| `04-ddd-ports-adapters.md` | the classical hexagon in Go |
| `05-pipeline-and-ai-harness.md` | plugin ensemble, ingestion lifecycle and AI harness in Go |
| `06-privacy-implementation.md` | the eight privacy layers in Go |

Stack assumed: Go ≥ 1.22, Chi, Cobra + Viper, MongoDB driver / database-sql,
jennifer for codegen, testify, testcontainers, golangci-lint v2.
