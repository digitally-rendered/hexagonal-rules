# The schema contract

In the schema-driven rungs of the ladder ([slip-stream](https://github.com/digitally-rendered/slip-stream),
[stellar-drive](https://github.com/digitally-rendered/stellar-drive) and applications built on them), a JSON Schema file
**is** the domain definition. This document is the contract those files
obey. The classical rung models the domain in code and uses schemas only at
the edges; its rules are the Level 0 rung's (`shared/05`).

## 1. One source of truth

- `schemas/*.json` (and `views/*.json`) generate **both halves of the stack**:
  backend models, repositories, endpoints; frontend types, validators, mappers,
  view descriptors. Nothing else is authoritative.
- Drift between a generated artifact and its schema is a **build failure**
  caught by the stack's **drift check**, not a runtime surprise. Every other
  file in this repository that says "the drift check" means the row below
  for its stack:

  | Stack | Drift check | Covers today | Adds under the frontend track (design, `shared/13` §2a) |
  |---|---|---|---|
  | Python (Level 3) | a generation script re-run in CI and diffed against the committed output | backend models, routers, SDK client; the application's `types.ts`, `schemas.ts`, `views.ts`, `apiTypes.ts` | default screens, route table, theme |
  | Go (Level 4) | golden-file tests per generator (`-update` regenerates deliberately) | structs, repositories, services, handlers, override stubs, OpenAPI, GraphQL SDL, SDK | the same frontend artifacts, from the emitted OpenAPI document |
  | TypeScript (Level 3.5) | `codegen:check`: regenerate and diff, fails CI on any difference | types, typed wrappers, OpenAPI, SDL, SDK, override stubs | default screens, route table, theme |

  The shared data hooks (`useEntity`, `useEntityList`, `useView`,
  `useMutation`) are hand-written once and are **not** generated, so no
  drift check covers them; the generated types they consume are covered.
  MCP tools, resources and prompts join the covered set in the stack whose
  application MCP server generates them (`shared/13` §2a says which).
- To add an entity: drop a schema file, restart (or hot-reload). Never
  hand-write the model class, CRUD, or endpoints for a schema-driven entity.
- Hand-crafted models are allowed only for: validation JSON Schema cannot
  express, computed properties or custom serialization, explicit relationship
  typing, or measured performance need. They are overrides (see the container
  rules), not replacements for the schema.

## 2. File naming and paths

| File | Schema name | URL segment | Model prefix |
|---|---|---|---|
| `order_item.json` | `order_item` | `/api/v1/order-item/` | `OrderItem` |

- Schema name is the file stem, `snake_case`.
- URL path is `kebab-case` (`name.replace("_", "-")`), done by the router, once.
- Model class names are `PascalCase` from the schema name.
- Collection/table name defaults to the schema name; `x-collection` overrides
  it (see §6).

## 3. Required structure

```json
{
  "title": "Pet",
  "version": "1.0.0",
  "type": "object",
  "required": ["name", "status"],
  "properties": { ... }
}
```

- `type` MUST be `object`. `title` and `version` SHOULD be present (`version`
  defaults to `1.0.0`). Check: the loader test registers a non-object schema
  and asserts `SCHEMA_INVALID`.
- Two file shapes are accepted by a conforming loader: the **envelope**
  (`{name, version, schema, …}`) and the **bare schema** (`title`/`version`
  at the root); storage is envelope-only.
- `required` lists create-time requirements for domain fields only.
- Reserved audit fields (below) MAY appear in `properties` for documentation
  and are ignored for input models. Listing them in `required` has no effect.

## 4. Reserved audit fields

Every persisted document carries these; the framework manages them and callers
never supply them:

| Field | Type | Meaning |
|---|---|---|
| `id` / `_id` | uuid | identity of **this version**; new on every write |
| `entity_id` | uuid | stable logical identity across versions |
| `schema_version` | string | schema version active when written |
| `record_version` | integer | starts at 1, increments per write |
| `created_at` | date-time | first creation, never changes |
| `updated_at` | date-time | every write |
| `deleted_at` | date-time or null | tombstone marker |
| `created_by` / `updated_by` / `deleted_by` | string | user audit trail |

See `shared/03-versioned-documents.md` for the semantics.

## 5. Generated model variants

For each schema the registry generates three models:

| Variant | Name | Fields | Use |
|---|---|---|---|
| Document | `{Pascal}Document` / `{Pascal}` | domain + audit | read/write persistence |
| Create | `{Pascal}Create` | domain only; `required` honoured | POST body |
| Update | `{Pascal}Update` | domain only; every field optional | PATCH body |

Each stack maps JSON Schema types to its native types in **one table** in
its language folder (one mapping function, no second site); `string/uuid`
and `string/date-time` map to the stack's UUID and timestamp types, never
to plain strings; `array` maps to a list of the resolved item type;
`default` becomes the field default; `enum` becomes a closed type where the
language has one. Check: a generated-model test round-trips a sample
payload per JSON Schema type and asserts the native type.

## 6. Vendor extensions (`x-*`)

Extensions are declarative policy on the generated surface. They are read once
at router-build time and must raise on malformed values; a typo must never
silently decide a policy question. Two tables: what a schema file may
declare (input), and what the OpenAPI document carries (output).

**Schema-file extensions (input; declared here; undeclared fails)**

| Key | Meaning | Rules | Status |
|---|---|---|---|
| `x-collection` | persist to a differently named collection | migration/disambiguation tool only; requires `x-collection-reason`; every code path that resolves a collection name uses the one registry accessor | shipped |
| `x-owner-field` | field holding the owning user id for ownership scoping | absent = scoped on `created_by` (default deny); string = scoped on that field; `null`/`false` = shared, requires `x-owner-reason`; prefer a Tier 2 view over `null` | shipped |
| `x-owner-reason`, `x-collection-reason` | human justification | required with the override they explain | shipped |
| `x-ui-widget`, `x-ui-group`, `x-ui-order`, `x-ui-hidden` | presentation hints for default screens | optional; closed vocabulary per key; never change validation or policy; a hint the generator does not know fails generation | frontend track, design (`shared/13` §2a); a loader that does not implement the track rejects them like any undeclared key until it declares them |

Add a new extension only with: a registry accessor, a fail-closed parser, a
test over every schema, and a line in this table. An undeclared `x-*` key
MUST fail schema registration (`SCHEMA_INVALID`), never warn; consumers
declare custom extensions in configuration. Check: a loader test registers
a schema carrying an unknown `x-*` key and asserts `SCHEMA_INVALID`.

View specs (`shared/03` §7) are separate files with plain keys; they are
not schema-file extensions and declare no `x-*` of their own.

**OpenAPI emission (output; produced by the backend, never written by hand)**

| Emitted key | Placed on | Source |
|---|---|---|
| every declared input extension above | the component schema or operation it was declared on | the schema file |
| `x-schema-version` | each Document, Create and Update component schema | the schema envelope's `version` |
| `x-view` | the view's read operation | the view spec file, copied whole (projection, filters, sort, limits, roles, scope) |
| operation ids | each operation | the registry's `<schema>_<operation>` names, the same names the MCP tools use |
| capability or role tags | each operation | the guards and view roles the registry resolved |

### 6a. The OpenAPI document is the contract for every downstream generator

Every row of the emission table MUST appear in the generated OpenAPI 3.1
document, and the document MUST be buildable **from files alone** (schema
loader → OpenAPI builder, no running application, no database), so that
pre-commit generation stays safe. The document is the only input any
downstream generator may read: typed clients, the agent surface's parity
test (`shared/13` §2) and, under the frontend track, default screens all
consume the document and never the backend's schema files or source. A
downstream generator that finds a required key missing fails with a named
error and never guesses. A backend that drops an extension on the way to
OpenAPI breaks a consumer it cannot see.

Check: a test loads every schema and view, builds the document with the
file-only builder, and asserts each emission-table row is present on the
corresponding operation or component schema; a second test asserts the
file-only document equals the one served at `/openapi.json` by a running
test engine.

## 7. Schema envelopes and versioning

- **Version lives in the body, not the URL.** The Go framework wraps schemas in
  an envelope `{name, version, schema}`; the Python framework reads `version`
  from the schema root. Clients request a version with the
  `X-Schema-Version` header; the request context carries it.
- Versions are semver. Multiple versions of one schema MAY coexist
  (`schemas/pet/1.0.0.json`, `2.0.0.json`); `latest` is the highest.
- Documents are always **written** at the current version, and
  `schema_version` MUST be written on every row (two reference
  implementations never wrote it, which made their migration layers fail on
  every read). Check: the hex check `schema version written` in the
  contract-fuzz suite, and the repository contract suite's create case
  asserting the field on the stored row. **Read-time migrations** run when
  `doc.schema_version != current`; they are registered in one migration
  registry.
- A request MAY select a version (`X-Schema-Version` or `?version`); the
  body is validated against **that** version's Create/Update variant and
  stored at latest after migration; the response is projected to the
  requested version while keeping audit fields.
- Widening an enum shared by several schemas changes the content hash of every
  consumer of that enum; expect cache busts (see
  `shared/06-evals-and-verification.md` §7).
- Hot reload: a file watcher MAY reload schemas without restart; in a
  multi-instance deployment, schema changes propagate through the persisted
  schema store (change streams), never through out-of-band file copies.

## 8. The registry

- The schema registry loads at startup and is a singleton (Python) or an
  engine-owned instance (Go). Tests MUST reset it between cases. Check: an
  autouse reset fixture (or per-test engine teardown), and one test that
  registers a schema in one case and asserts it is absent in the next.
- The registry is the only reader of schema files. Everything else asks the
  registry: names, versions, models, collection names, owner fields.
- Everything derived from a schema is derived at startup, once. Request-time
  code never parses schema JSON.

## 9. Schema-enforced generation

When an LLM produces structured output, the schema is passed as a sampler
constraint (`format=` / JSON-schema mode), not recovered by regex afterwards.
Pydantic (or equivalent) validation is the second line, never the first. The
schema is part of the cache key for that stage.

## 10. One authority per vocabulary

Closed vocabularies that appear in schemas (`enum`), prompts, gates and UIs are
defined once in code and the schema files are generated or validated against
that definition. A test pins every site that uses the vocabulary.
