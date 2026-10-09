# TypeScript / React rules

Read `shared/` first. The frontend is a hexagon of its own: domain components
are the entities, hooks are the use cases, port interfaces define the
boundary, and pages and service adapters are the primary and secondary
adapters.

| File | Source |
|---|---|
| `01-react-hexagonal.md` | a classical DDD application's React hexagonal rules and frontend patterns |
| `02-generated-layer.md` | a schema-driven application's frontend tiers, type generator, data hooks, case convention |
| `03-testing.md` | both |
| `04-conventions.md` | both |
| `05-ui-platform-rules.md` | both, plus the mobile/PWA and onboarding specs |

Stack assumed: React 18/19, TypeScript strict, Vite, MUI (v7 where noted),
React Router, React Hook Form + Zod, Vitest + Testing Library, MSW,
Playwright.
