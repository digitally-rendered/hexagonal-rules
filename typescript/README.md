# TypeScript rules

Read `shared/` first. Files 01–05 are the frontend hexagon: domain
components are the entities, hooks are the use cases, port interfaces define
the boundary, and pages and service adapters are the primary and secondary
adapters. Files 06–11 are the Node backend: the schema-driven framework
([Syntact](https://github.com/digitally-rendered/Syntact), in flight), its testing and performance standards, and
the classical, pipeline and privacy rungs in TypeScript.

| File | Source |
|---|---|
| `01-react-hexagonal.md` | a classical DDD application's React hexagonal rules and frontend patterns |
| `02-generated-layer.md` | a schema-driven application's frontend tiers, type generator, data hooks, case convention |
| `03-testing.md` | both |
| `04-conventions.md` | both |
| `05-ui-platform-rules.md` | both, plus the mobile/PWA and onboarding specs |
| `06-schema-driven-framework.md` | [Syntact](https://github.com/digitally-rendered/Syntact) design |
| `07-backend-testing.md` | Syntact testing strategy and the reference toolkits |
| `08-performance.md` | Syntact benchmark harness |
| `09-node-ddd-ports-adapters.md` | port of `python/01` |
| `10-node-pipeline-and-ai-harness.md` | port of `python/03` and `shared/09`–`11` |
| `11-privacy-implementation.md` | port of `shared/08` |

Frontend stack: React 18/19, TypeScript strict, Vite, MUI (v7 where noted),
React Router, React Hook Form + Zod, Vitest + Testing Library, MSW,
Playwright. Backend stack: Node ≥ 22 (and Bun), Hono or Fastify, Ajv,
Mongo driver or Kysely, pino, Vitest, fast-check, dependency-cruiser.
