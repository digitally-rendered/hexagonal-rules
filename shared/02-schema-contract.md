# The schema contract

In the schema-driven rungs of the ladder ([slip-stream](https://github.com/digitally-rendered/slip-stream),
[stellar-drive](https://github.com/digitally-rendered/stellar-drive) and applications built on them), a JSON Schema file
**is** the domain definition. This document is the contract those files
obey. The classical rung models the domain in code and uses schemas only at
the edges; its rules are in `python/01-ddd-ports-adapters.md`.

## 1. One source of truth

- `schemas/*.json` (and `views/*.json`) generate **both halves of the stack**:
  backend models, repositories, endpoints; frontend types, validators, mappers,
  view descriptors. Nothing else is authoritative.
- Drift between generated halves is a **build failure** (`codegen:check` in
  CI), not a runtime surprise.
- To add an entity: drop a schema file, restart (or hot-reload). Never
  hand-write the Pydantic model, CRUD, or endpoints for a schema-driven entity.
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
  defaults to `1.0.0`).
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

Type mapping: `string`→`str`, `string/uuid`→UUID, `string/date-time`→datetime,
`integer`→int, `number`→float, `boolean`→bool, `array`→list of resolved item
type, `object`→dict. `default` becomes the field default. Go generates the
equivalent structs plus enum types.

## 6. Vendor extensions (`x-*`)

Extensions are declarative policy on the generated surface. They are read once
at router-build time and must raise on malformed values; a typo must never
silently decide a policy question.

| Key | Meaning | Rules |
|---|---|---|
| `x-collection` | persist to a differently named collection | migration/disambiguation tool only; requires `x-collection-reason`; every code path that resolves a collection name uses the one registry accessor |
| `x-owner-field` | field holding the owning user id for ownership scoping | absent = scoped on `created_by` (default deny); string = scoped on that field; `null`/`false` = shared, requires `x-owner-reason`; prefer a Tier 2 view over `null` |
| `x-owner-reason`, `x-collection-reason` | human justification | required with the override they explain |

Add a new extension only with: a registry accessor, a fail-closed parser, a
test over every schema, and a line in this table. An undeclared `x-*` key
MUST fail schema registration (`SCHEMA_INVALID`), never warn; consumers
declare custom extensions in configuration.

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
  every read). **Read-time migrations** run when `doc.schema_version !=
  current`; they are registered in one migration registry.
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
  engine-owned instance (Go). Tests MUST reset it between cases.
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
