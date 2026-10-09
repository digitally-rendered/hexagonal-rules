# Performance and benchmarks (TypeScript / Node)

Source: [Syntact](https://github.com/digitally-rendered/Syntact) benchmark harness (in flight), porting the micro and
load benchmarks of the two reference frameworks. The population-counting
rule of `shared/06` §10 applies to every number.

## 1. Where benchmarks live

- Each package keeps its own `bench/` beside the code; a `benchmarks/`
  workspace package holds the HTTP load harness, compat runs, results and
  baselines.
- Micro benchmarks use the test runner's bench mode and write JSON; HTTP
  load uses a programmatic load generator plus the shared k6 scripts ported
  verbatim from the reference frameworks so the three implementations are
  compared on identical requests.

## 2. Micro suites (each with a committed baseline)

| Area | Cases |
|---|---|
| schema | register 1/10/50 envelopes; 50-field schema; cached get; loader over 10 files; validator compile per variant; `$ref` resolve |
| query | parse, validate, Mongo translate, SQL translate, sort parse, cursor encode/decode |
| executor | full pipeline with 0/5/50 hooks on the memory repository; specificity resolve with 1k registrations; bus emit with 0/10/100 subscribers |
| repository (memory) | create/update/list 10k documents; deep-merge; ETag |
| http | dispatch per driving adapter for create/get/list with middleware on and off; envelope and problem serialisation; projection |
| streaming | publish 100/1k/10k; bridge forward; fan-out 1/3/5; marshal |
| graphql | build 1/3/5 schemas; versioned build; query, list, mutation, update, parallel |
| mcp | list schemas, get schema, describe entity, list versions, schema DAG |
| codegen | per schema; 50 schemas |

## 3. The ratchet

- Baselines are committed JSON; `bench:check` compares with a stated
  tolerance (15%) and fails on regression. Numbers may improve or stay;
  re-baseline deliberately in the same commit with the reason.
- CI posts the comparison on the PR; micro regressions block once the
  first baseline is committed; HTTP load numbers are informational.

## 4. HTTP load and compat

- Scenarios: smoke, load, stress, breaking; thresholds p95 < 500 ms and
  failed < 1% (a 404 after delete is expected, not a failure).
- GraphQL and stream load scripts.
- `compat_test`: the three implementations on fixed ports receive identical
  requests; `compat_errors < 1`; every intentional difference is listed in
  a compat document.
- `measure`: boot-to-health, RSS baseline and peak, CPU; Node and Bun;
  optional CPU and memory limits via containers.
- A compose file with the database and the three apps for compat runs.

## 5. Fuzz

OpenAPI-driven REST fuzz (positive, type-swap, unknown field, constraint
break) with the hex checks; GraphQL (introspection-driven queries and
mutations, depth bombs, invalid enums); MCP (malformed tool params over
stdio); stream (corrupted payloads, topic format, ordering, multi-version).
**Zero 500s** is blocking.

## 6. Reporting

Every published number names its population (dataset size, schema count,
hook count, adapter, runtime, machine) and the baseline it is compared to.
