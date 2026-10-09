# Privacy layering: TypeScript / Node implementation notes

How the eight layers of `shared/08-data-privacy-layering.md` land in a
TypeScript backend.

| Layer | Implementation |
|---|---|
| L0 storage tiers | `.env` validated once by Zod; secrets never in `process.env` reads outside config; `.gitignore` plus a secret scanner in pre-commit; private directories outside the repo |
| L1 classification | `domain/model/shared/data-classification.ts`: `const REGISTRY: Record<FieldId, ReadonlySet<Tier>>`; a script lists persisted fields (from table types or schemas) without an entry; CI gate once green |
| L2 audience / privilege | one `classify(participants)` function exported from one module; every consumer imports it; a lint rule forbids re-implementing the role tables |
| L3 ownership scoping | applied inside the endpoint factory from `x-owner-field`; fail-closed branches; security tests parametrised over every schema in the registry with two least-privileged identities |
| L4 ReBAC | `AuthorizationPort` interface in `domain/ports`; `AuthorizationService` in `domain/services` with the priority chain; repositories take `principal` and apply isolation in the query builder; per-request relationship cache on `request.state` |
| L5 delegation | `Principal` type with `isObo`, `agentId`, `oboScopes`; auth plugin extracts the delegation claims; scope intersection in the authorization service; admin override never inherited |
| L6 consent | `ConsentRecord` as a frozen object; repository port with `append` and `listByUser` only; a `requireActiveConsent(principal)` guard in every write use case that persists personal information |
| L7 encryption | `KeyManagementPort` in `application/ports/secondary`; envelope codec in `infrastructure/adapters/secondary/crypto/envelope.ts` using `node:crypto` AES-256-GCM with the header as AAD; encrypted columns via Kysely/Drizzle custom column types or Prisma client extensions (`$extends` result/query hooks) so repositories are unaware; request-scoped DEK cache in `AsyncLocalStorage`, never persisted or logged; blind index as HMAC-SHA256 column |
| L8 audit | two append-only tables; an `audit(entry)` port; a test drives a real request through the app and asserts the row exists; evidence exporter reads only |

Browser-side rules for delegated tools, metadata-by-default and
confirmation on privileged content are in `typescript/05-ui-platform-rules.md`.
