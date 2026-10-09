# The generated layer and data hooks

Source: a schema-driven application's frontend. Applies when the backend is schema-driven
(`shared/02-schema-contract.md`). The frontend tier rule mirrors the backend.

## 1. Frontend tiers

| Tier | What | You write |
|---|---|---|
| 1 | types + Zod validators for an existing backend entity | nothing: generated from `schemas/*.json` |
| 2 | fetching/listing/mutating an entity or view | nothing: `useEntity`, `useEntityList`, `useView`, `useMutation` |
| 3 | genuine UI behaviour (wizard, drag-and-drop, chart, PDF preview, rich text, agent UI) | hand-written, through generated types and shared hooks |

**The test:** delete the UI behaviour; if only fetch–map–render remains, it is
Tier 1 or 2. Enforced by the drift ratchet (`inline_case_mapping`,
`apiclient_in_deps`, `handwritten_fetch_state` gated;
`handwritten_interfaces`, `frontend_page_loc`, `generated_frontend_loc`
tracked but not gated).

## 2. `src/generated/` — two sources, one per tier

| Files | Source | Tier |
|---|---|---|
| `types.ts`, `schemas.ts`, `views.ts` | schema and view JSON files, read from disk | 1, 2 |
| `apiTypes.ts`, `apiSchemas.ts` | the live OpenAPI spec built in-process | 3 |

- Tier 1/2 stay file-derived: no app import, safe in pre-commit, and view
  descriptors (`roles`, `filterParams`, limits) have no OpenAPI representation.
  Once the backend emits `x-view` and the other extensions into the document
  (`shared/02` §6a), the split collapses to one spec-derived source; that is
  the input model of the frontend track (`typescript/12`).
- Tier 3 is spec-derived because hand-written endpoints have no schema file;
  before this there was zero cascade from a changed response model.
- Name collisions are **renamed, never merged**: controller-qualified names for
  duplicate short names; an `Api` prefix when a Tier 3 model's bare name
  collides with a Tier 1/2 export. Shapes were verified to differ.
- `npm run codegen:check` regenerates and diffs in CI; drift is a build
  failure.
- Never hand-declare an `interface` for a shape a backend schema already
  describes.

## 3. Data hooks

```ts
useEntity('assessment', id)                 // GET /api/v1/assessment/{id}
useEntityList('case', { status: 'open' })   // GET /api/v1/case/?…
useView('my-queue', params)           // Tier 2 view endpoint, typed by ViewDescriptor
useMutation(...)                            // POST/PATCH/DELETE with mapping
```

- Built on one `useAsyncQuery(fn, deps, { enabled, errorMessage })` that owns
  loading/error, memoises the client, and applies `fromApi`/`toApi` mapping so
  components only ever see `camelCase`.
- A falsy id disables the fetch rather than requesting `/undefined`.
- Kebab-case path derivation (`entity.replace(/_/g, '-')`) lives in one helper
  mirroring the backend router.

## 4. Case convention

- Backend: `snake_case` bodies and query params; `kebab-case` paths.
- Frontend: `camelCase` everything; components `PascalCase.tsx`; utilities
  `camelCase.ts`; CSS classes `kebab-case`.
- **No case-conversion middleware when a codegen exists.** One generated mapper
  per schema, produced beside the type, so conversion cannot drift from the
  field list. Reading `.entity_id` or `.created_at` in a page or component is a
  violation regardless of which layer currently owns the mapper.
- When there is no codegen (classical backend), an axios case-converter at the
  adapter boundary is acceptable, and the rule becomes "conversion only in the
  adapter".
- Third-party payloads the codegen does not own are the one Class B exception.

## 5. The API client

- Single `apiClient` with base `/api/v1/`, memoised by `useApiClient()`.
- **`useApiClient()` never appears in a dependency array.** Depend on the
  primitive parameters that should trigger a refetch. This shape caused a real
  infinite-render outage.
- Thin `fetch` wrapper or axios; one place for auth header injection and error
  typing.
