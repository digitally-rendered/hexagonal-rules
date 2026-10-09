# Versioned documents (append-only persistence)

Shared by [slip-stream](https://github.com/digitally-rendered/slip-stream), [stellar-drive](https://github.com/digitally-rendered/stellar-drive) and the applications
built on them. The classical SQL rung uses `is_deleted` soft-delete and a
`version` column for optimistic concurrency instead; those rules are in
`python/01-ddd-ports-adapters.md`.

## 1. The invariant

**Never mutate a stored document. Every write inserts a new version.**

| Operation | Effect |
|---|---|
| create | new `entity_id`, `record_version = 1`, new `id`, `created_at = updated_at = now`, `created_by = user` |
| update | read current, deep-merge patch, `record_version + 1`, new `id`, `updated_at = now`, `updated_by = user`; insert; never modify existing |
| delete | read current, `record_version + 1`, new `id`, `deleted_at = now`, `deleted_by = user`; insert tombstone |
| get | latest `record_version` for `entity_id`; `None`/404 if that version is a tombstone |
| list | group by `entity_id`, take max `record_version`, drop tombstones, then filter, sort, paginate |

- Updates and deletes **authorize against the current version before writing**.
  Under append-only, an unauthorized write is not rolled back; it is a
  permanent extra version.
- A compound unique index on `(entity_id, record_version)` is created on every
  startup (`EnsureIndexes` / `ensure_indexes`, idempotent).
- Reads always return a typed document model; raw dicts never leave the
  repository.

## 2. Why this is a correctness control

A raw `find()` on a versioned collection returns **every historical version
plus tombstones**. Every P0 defect found in the schema-driven repos' audits
lived in hand-written code that bypassed the versioned read path; the
generated path produced none. Hence:

- **MUST NOT** call `update_one`, `delete_one`, `replace_one`, or raw
  `find`/`find_one` on a versioned collection outside the repository adapter.
  Enforced by project lint rules (raw read, in-place mutation) and the drift
  ratchet.
- **Exception (Class B):** a collection that is insert-only by nature (access
  logs, audit entries, OCR records) may be written directly; it is listed in
  the mutation allowlist with a reason.
- **Exception (Class B):** a Tier 3 aggregation the versioned helper cannot
  express may read raw, **and still filters tombstones explicitly**, with the
  reason at the site.
- Roadmap rung 1: the database handle handed to controllers should be a
  repository facade with no `.find()`. The raw handle in DI is why the debt
  exists.

## 3. Bulk operations

- `bulk_create`, `bulk_update`, `bulk_delete` follow the same per-item
  semantics and preserve input order.
- Atomic versus best-effort is an adapter property and is documented on the
  adapter; the request context carries `atomic` and per-item `bulk_index`.
- Lifecycle events fire for bulk operations (`pre/post_bulk_*`), not once per
  item.

## 4. Query DSL

- Clients never send raw database queries. Filters use a Hasura-style `where`
  with an allowlisted operator set (`_eq`, `_neq`, `_gt`, `_gte`, `_lt`,
  `_lte`, `_in`, `_nin`, `_like`, `_ilike`, `_contains`, `_startswith`,
  `_endswith`, `_exists`, `_is_null`, `_and`, `_or`, `_not`).
- The DSL is parsed and validated in the core and translated per backend in the
  adapter (aggregation pipeline for Mongo, `WHERE` for SQL).
- Pagination supports offset (`skip`/`limit`) and cursor (`first`/`after`,
  `last`/`before`); the response carries `total` and `has_more` or `page_info`.

## 5. Conditional requests

- Every document carries an ETag derived from its version.
- `If-None-Match` → 304; `If-Match` mismatch → 412. The ETag travels through
  the request context, never through globals.

## 6. UUID storage (Mongo)

- UUIDs are stored as BSON Binary with a fixed representation; the base
  document normalises Binary/str/UUID on read by field-name convention
  (`id`, `_id`, `entity_id`, `*_id`, `*_ids` are UUIDs; `*_by` stay strings).
- Mock drivers store UUIDs as strings; tests must not assert on the raw
  representation.

## 7. Views (Tier 2)

A **view spec** is a JSON file declaring: `entity`, `path`, `roles`,
`scope` (ownership field, or absent for a shared read), `constant_filters`,
parameterised `filters` (`param`, `field`/`fields`, `op`), `sort`,
`pagination` (`default_limit`, `max_limit`, `include_total`), `projection`.

- Views read through the latest-active path, so duplicate-version and
  tombstone leaks are impossible by construction.
- A genuinely public read is a view that declares `roles` and omits `scope`,
  not an entity with ownership turned off.
- A caller with no resolvable id gets a match-nothing filter, never an
  unscoped query.
