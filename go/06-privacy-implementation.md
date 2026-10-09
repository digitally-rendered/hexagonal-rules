# Privacy layering: Go implementation notes

How the eight layers of `shared/08-data-privacy-layering.md` land in a Go
service.

| Layer | Implementation |
|---|---|
| L0 storage tiers | config struct loaded once; secrets via env or keyring; `gitleaks` in pre-commit; private directories outside the module |
| L1 classification | `domain/shared/classification.go`: `var Registry = map[FieldID]TierSet{…}` with a `Strictest(tags)` resolver; a `go test` enumerates persisted struct fields by tag and fails on an unclassified one |
| L2 audience / privilege | one `audience.Classify(participants)` function; every consumer imports it; a `go/ast` test fails on a second role table |
| L3 ownership scoping | applied in the generic handler from `x-owner-field` resolved once per schema; fail-closed; security tests iterate the registry with two least-privileged principals |
| L4 ReBAC | `port.Authorizer` interface in the domain; `AuthorizationService` with the priority chain; repositories take the principal and apply isolation in the query; per-request relationship cache in `context.Context` via `internal/ctxkey` |
| L5 delegation | `Principal{IsOBO, AgentID, OBOScopes}` set by the auth middleware from token-exchange claims; scope intersection in the authorizer; admin override never inherited |
| L6 consent | `ConsentRecord` value type; repository interface with `Append` and `ListByUser` only; `RequireActiveConsent` guard in every write use case that persists personal data |
| L7 encryption | `port.KeyManager` in `app/port`; envelope codec in `adapter/driven/crypto/envelope.go` with `crypto/aes` + `cipher.NewGCM` and the header as additional data; encrypted columns via `sql.Scanner`/`driver.Valuer` wrapper types (`EncryptedString`) so repositories are unaware; request-scoped DEK cache in context, never persisted or logged; blind index as an HMAC-SHA256 column |
| L8 audit | two append-only tables behind `port.AuditStore`; a test drives a real request through the router and asserts the row; evidence exporter reads only |
