# The generated frontend track: screens from the OpenAPI document

Status: a design for a fourth public track, not yet a shipped framework. It
extends `typescript/02` (types and hooks are generated today) to whole
default screens, so a feature exists for a human from the same `generate`
run that gives it to an agent (`shared/13`). The backends emit the
contract; this track consumes it. One frontend generator serves the
Python, Go and TypeScript backends because all three emit OpenAPI 3 from
the same schemas.

## 1. Input: the OpenAPI document, and nothing else

- The generator reads **one OpenAPI 3.1 document**, never the backend's
  schema files or source. The document is produced by a **file-only build
  step** (schema loader → OpenAPI builder; no running application, no
  database), so generation stays pre-commit safe, which is the property
  `typescript/02` §2 protects today with file-derived Tier 1/2 types. The
  served `/openapi.json` is the same document and a test asserts the two are
  equal (`shared/02` §6a); the generator may read either, and pre-commit
  reads the file-built one. This removes the two-source split of
  `typescript/02` §2 once the backends carry views and extensions into the
  document.
- Required in the document: component schemas for Document, Create and
  Update variants with `x-schema-version`; `x-view` descriptors on view
  operations; `x-owner-field`; the `x-*-reason` texts; `x-ui-*` hints;
  operation ids that equal the registry's `<schema>_<operation>` names (the
  same names the MCP tools use); the capability or role tags per operation.
- A document missing any of these fails generation with a named error; the
  generator never guesses a form from a bare schema.
- Tier 3 operations appear as ordinary operations with request and response
  schemas; they generate typed actions and a stub screen.

## 2. Output: a complete default feature per schema

| From | Generated (universal match) | Override point |
|---|---|---|
| Document schema | `types.ts`, `schemas.ts` (zod), the entity card and detail page | field renderer, detail layout |
| Create and Update schemas | create and edit forms (React Hook Form + zod), field order and grouping from `x-ui-group` and `x-ui-order` | field widget, form layout, submit flow |
| `x-view` descriptor | list and grid pages with the view's filters, columns, sort and pagination; export | column renderer, row actions, filter bar |
| operations and capability tags | typed client, `useEntity`, `useEntityList`, `useView`, `useMutation`, action buttons shown only when the capability is present | action component |
| Tier 3 operations | typed action hook and a stub screen (`<Operation>Screen.generated.tsx`) | the whole screen |
| all schemas | route table, lazy routes, navigation entries, breadcrumb titles, empty states, `data-testid` on every interactive element, `axe`-clean markup | navigation order, titles |
| `x-*-reason`, field titles, descriptions | help text, tooltips, column headers, i18n message keys with defaults | translations |
| MCP tools of the same operations | the "ask the agent" affordance: a `why_` rationale panel and a simulate-then-apply flow next to the form (`shared/13` §4) | the panel |

Generated files live under `src/generated/` and are never edited; the drift
check (`shared/02` §1, here `codegen:check`) regenerates and diffs in CI.

## 3. The override model: a component registry with specificity

Mirrors the backend registry (`shared/01` §6, `typescript/06` §3) so one
mental model covers both sides.

- A **component registry** keyed by `(schema, operation | field | slot,
  scope)` where scope is `{version?, role?}`; the universal match is the
  generated component.
- Which registration wins is the scope resolution of `shared/01` §6a, the
  same algorithm as the backend with **role in place of channel** as the
  second axis (version+role 4, role 3, version 2, universal 1, mismatch
  excluded); a component takes one match like a handler; duplicate
  registrations at the same specificity are a build error. Check: the
  registry reuses the backend's property test (resolution is a total stable
  order) over generated registries.
- Override granularity, from narrow to wide: field widget → field group →
  form or list section → whole screen → whole feature. Prefer the
  narrowest; a whole-screen override needs a reason comment at the site
  (Class B, `shared/04`).
- Overrides are ordinary React files in `src/features/<schema>/` registered
  with `registerComponent(...)`; they receive the same typed props the
  generated component would. The generator never writes into `features/`,
  and re-running it never changes an override.
- A hand-written screen still uses the generated hooks and types; an
  override that fetches on its own or re-declares a shape fails the drift
  ratchet (`typescript/02` §1).
- The registry is the port between the generator and the app. The renderer
  library sits behind it.

## 4. Renderer: the component library decision

Decision: **MUI remains the default renderer**, pinned to one major, with
the theme in CSS-variables mode so design tokens bind directly
(`typescript/13`). The renderer is reached only through the registry's
component contract, so an application may choose another library as a
Class B override per app, never per component (`typescript/04`: no mixing
inside a component).

| Candidate | For | Against | Verdict |
|---|---|---|---|
| MUI (with the data grid) | two existing applications and their tests; full form control set; data grid with filtering, sorting, virtualisation and editing; CSS-variables theming; mature accessibility | the grid's advanced features are a paid tier; dense visual default needs theming to look like a product | **default renderer** |
| Mantine | good forms and hooks; lighter than MUI | no comparable data grid; smaller ecosystem; a second library to learn | not now |
| Radix primitives + Tailwind (shadcn-style) | you own the component code; tokens flow as CSS variables with no theme layer; best fit for bespoke design | no grid or form system: assembly with TanStack Table and React Hook Form; more to generate and maintain | allowed as a per-app override; a candidate second renderer once the registry is stable |
| Ant Design with its CRUD components | the strongest out-of-the-box CRUD and admin screens; a complete token system | opinionated design language; heavy; two themes in one product is painful | not now |
| Chakra | good token model | no grid | not now |

The grid is the deciding component for a generated CRUD frontend. If the
paid grid tier is not acceptable, the list and grid generator targets
TanStack Table under MUI table primitives and loses inline editing and
virtualisation; record the choice in the application's design decisions.

## 5. The React hexagon is unchanged

Generated components are domain components (props only); generated hooks
are the application layer; the generated client is the secondary adapter;
pages compose; the registry is the port between generator and app
(`typescript/01`). The generated tree and the override tree are split by
layer so the fitness tests can classify every file:

| Directory | `typescript/01` layer | Alias | May import |
|---|---|---|---|
| `src/generated/domain/` (field renderers, cards, forms, list cells) | `domain/components` | `@domain/generated/*` | `@domain/*` only; never a hook, the client or the registry |
| `src/generated/application/` (typed action hooks, the shared data hooks' typed wrappers, route table) | `application/hooks` | `@application/generated/*` | `@domain/*`, `@ports/*` |
| `src/generated/adapters/` (typed client over `apiClient`) | `adapters/secondary` | `@adapters/generated/*` | `@domain/*`, `@ports/*`, `infrastructure/api` |
| `src/generated/registry.ts` (component contract, `registerComponent`) | `ports` | `@ports/component-registry` | domain types only |
| `src/features/<schema>/components/` (override components) | `domain/components` | `@domain/features/*` | as domain components; props only |
| `src/features/<schema>/hooks/` (override hooks) | `application/hooks` | `@application/features/*` | `@domain/*`, `@ports/*`, `@application/generated/*` |
| `src/features/<schema>/index.ts` (the `registerComponent(...)` calls) | `adapters/primary` (composition) | — | everything; it is wiring |

The import rule is `typescript/01` §1's for the layer each directory maps
to; the only addition is that `features/` may import `generated/` and
`generated/` never imports `features/` (the generator does not know the
overrides exist). `typescript/01` §1 must carry the same two subtrees in its
layer map for this table to be enforceable. The AST fitness tests run over
`src/generated/` and `src/features/` as over any other code. Accessibility, error presentation, roles, mobile and i18n
rules apply to generated output (`typescript/05`), and the generator is
the place to fix a violation once for every screen.

## 6. Parity with REST and MCP

The parity test of `shared/13` extends to screens: for every operation in
the document, a test asserts a REST route, an MCP tool and a generated
action or screen exist, agree on schema version, reject the same invalid
payloads (zod on the client, the executor on the server, the tool schema
for agents), and hide or deny under the same missing capability.

## 7. Tests

| Concern | Check |
|---|---|
| generator input | contract test: a document missing `x-view`, `x-ui-*`, operation ids or capability tags fails with a named error |
| drift | the drift check (`shared/02` §1, `codegen:check`) over `src/generated/` |
| pre-commit safety | the file-only OpenAPI build runs with no server and no database in the pre-commit hook; a test asserts its output equals the served `/openapi.json` |
| override integrity | duplicate specificity fails the build; an override not using generated hooks or types fails the ratchet; the generator leaves `features/` untouched (snapshot of `features/` before and after `generate`) |
| default screens | every generated form validates with the generated zod schema; every list renders the view's columns; `axe` passes on every generated page; every interactive element has `data-testid` |
| parity | one test per operation across REST, MCP and screen |
| renderer isolation | an AST test: `src/generated/` imports the renderer only through the registry's component contract |
| live | Playwright: a generated feature's full workflow with no override, then the same with an override registered |
