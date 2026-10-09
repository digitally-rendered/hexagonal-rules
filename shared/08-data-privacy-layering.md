# Data privacy layering

Privacy is a layered design concern, not a feature. Every layer below holds
in its own right; together they make "who may see what, and what proves it"
answerable at every point in the stack. Distilled from the application
sources (relationship-based authorization, delegation, consent ledgers,
authorization audit trails, envelope encryption and crypto-erasure, data
classification, compliance evidence, ownership scoping on generated
surfaces, security invariant tests) and from a personal knowledge workspace
(audience classification, storage tiers, read-only sources).

## 1. The layers

```
L0  Storage tiers        what is allowed to exist where (local-only, private repo, derived, secrets)
L1  Classification       what each field/item is (PII, privileged, confidential, protected-party data…)
L2  Audience             who already holds it / who may ever see it (derived from who is on it)
L3  Ownership scoping    default-deny row access on the generated surface
L4  Relationship access  ReBAC: owner, assigned professional, counterparty, admin override, delegate
L5  Delegation           an agent acts as a principal, never with more than the principal
L6  Consent              an append-only ledger of what was agreed, when, under which policy text
L7  Encryption           envelope encryption keyed per tenant/user; erasure by key destruction
L8  Audit + evidence     every access decision and relationship change recorded; evidence packaged read-only
```

Each layer is implemented behind a port in the core and an adapter outside
it. Domain entities never know a field is encrypted, who may read a row, or
how consent was captured.

## 2. L0 — Storage tiers

| Tier | Holds | Rules |
|---|---|---|
| Local only, never synced | raw message databases, ad-hoc exports, full dumps | lives under a `~/<project>-private` style directory; never in git, never in cloud sync; opened read-only |
| Secrets | app passwords, tokens, key material | one `.env` or keyring outside every repo; never printed, copied, or committed; the user edits it themselves |
| Private versioned record | originals by hash (LFS), configs, working notes, generated views | private repo; every change has a date and author; privileged notes under a marked folder |
| Derived | search indexes, model databases, caches | rebuildable from the record; not in git; refuse to shrink; keep history |
| Code | collectors, indexers, rules, skills | separate repo; contains no real data; fixtures are fictional |

- **Code here, data elsewhere.** The code repo never contains real data; the
  data repo never needs to run the code.
- **Sources are read-only.** Nothing writes back to a mailbox, a chat
  database, or a drive. Originals are write-once by SHA-256 with a hash-chained
  custody log; derived files can be rebuilt; indexes refuse to replace a
  larger index with a smaller one without an explicit flag. The full item
  lifecycle and the defensibility rules are in `second-brain/03`.
- **Masking by default**: account numbers to the last four; full card or
  identity numbers flagged in provenance and redacted in any produced copy.
- **No remote AI on private data unless disclosed.** Embeddings run locally;
  when a cloud model will read material, say so up front, and treat
  privileged material as needing the responsible professional's say-so.

## 3. L1 — Classification

- A **classification registry** is a static, versioned module in the domain:
  identifier → `frozenset` of tiers (`PII`, `PRIVILEGED`, `CONFIDENTIAL`,
  `PROTECTED_PARTY_DATA`, …). Tags, not a single enum: one field can be PII
  and protected-party data at once.
- Handling resolves to the **strictest applicable rule** across the tags
  present. Privileged and confidential override even an approved admin
  access grant.
- Every new persisted field is classified when it is added. A read-only audit
  script reports unclassified fields; it is a CI gate once green.
- Classification feeds encryption (which fields get an encrypted column
  type), authorization (which branches deny), retention, and audit.

## 4. L2 — Audience and privilege

**Audience and privilege are derived from who is on an item, never from
keywords.** The party model is generic: the user, the user's own advisor
(a professional whose communications with the user are privileged), the
other side (a counterparty and their advisors and associates), neutral
professionals (mediators, coordinators, evaluators engaged by both sides),
and everyone else.

| Privilege | When |
|---|---|
| `advisor_client` | the user's own advisor is on the item and the other side is absent; or a document marked privileged; with third parties present the basis says "possible waiver: advisor to review" and it is still withheld |
| `mediation` | a neutral mediator is on the item |
| `none` | everything else; a neutral professional is not privileged; an unlicensed helper is not an advisor |

| Audience | When (first match) | Use |
|---|---|---|
| `shared_with_other_side` | the counterparty, their advisors or associates are on it | safe base for drafting; they already have it |
| `privileged` | advisor–client and only own advisors | advisor only; never into anything for the other side |
| `neutral_professional` | a neutral professional, other side absent | check with the advisor before use |
| `private` | the user's own material and notes to self | not privileged, not yet disclosed; may become disclosable |
| `third_party` | anyone else, including unknown senders | review |

- One classification function, used by every consumer (index, generated
  views, export, read-only servers). Nothing re-implements it.
- When one thread carries several explicit audiences, the most restrictive
  wins, in a fixed order.
- Each audience is a separate output (one generated view, one server scope).
  Restricting a server to an audience is a hard limit: out-of-scope items are
  invisible to every tool, not filtered per query.
- Privileged rows are **withheld by default** from any export; counts of
  withheld rows are reported, never their content; a claim citing a withheld
  row keeps the claim and drops the pointer.
- A forwarded privileged thread with a third party on it is `private`, not
  `privileged`; the advisor reviews waiver.
- Roles that are not explicitly mapped stay `unknown` and are listed; they
  are never guessed.

## 5. L3 — Ownership scoping (generated surface)

- Every generated by-id and list endpoint is **owner-scoped by default**:
  privileged roles reach any row; everyone else only rows whose owner field
  (`x-owner-field`, default `created_by`) equals their id.
- Default is deny because the opposite default exposed every entity,
  sensitive data included, to any authenticated stranger. An opt-in marker
  would have left every un-annotated schema open; an opt-out marker leaves
  it safe and merely inconvenient.
- Fail closed: empty owner → refused; caller without id → match-nothing on
  list; PATCH/DELETE authorize against the current version before writing;
  malformed marker raises.
- A shared entity is a Tier 2 view with explicit `roles` and no `scope`, not
  an entity with scoping turned off.
- Tests: the ownership invariant runs over **every** aggregate with two users
  of the least-privileged role (owner vs stranger), so a 200 for the stranger
  cannot be a role override; the role matrix is derived from the installed
  role gates, not hand-maintained; every resource-addressing route names its
  protection mechanism or fails.

## 6. L4 — Relationship-based access (ReBAC)

- One `AuthorizationPort` in the domain (`can_access_<resource>(user,
  resource_id, action)`, `can_manage_<scope>_members`) returning a structured
  `AuthorizationResult{allowed, reason, relationship}`. It replaces
  per-controller access-check duplicates.
- Evaluation order for a resource: platform admin override → owner → active
  professional–client relationship → counterparty (read-only on explicitly
  shared data) → organization membership (when memberships exist) → deny.
- Denials do not distinguish "does not exist" from "not allowed" at the
  port; the transport layer picks one posture (`403`/`404`) per project and
  keeps it.
- Data isolation applies **at the repository query level** so out-of-scope
  rows are never loaded. Organization scoping is a parameter on repository
  methods from day one, even when there is one organization.
- Relationships (professional–client, counterparty assignment, grants) are
  explicit, typed records with creation path, status, timestamps, and
  termination; access changes on the next request after a change.
  Retroactive grants (engaging a professional exposes existing records) are
  explicit.
- Admin access to record **contents** needs an owner-approved, time-bounded
  grant recorded as its own aggregate; metadata access does not.
- Resolved relationships are cached per request only.

## 7. L5 — Delegation (On-Behalf-Of)

- An AI agent acts under a human principal through a delegation record:
  principal, agent client id, scopes, expiry, revocation. A delegation needs
  at least one scope and a valid agent id; expired or revoked is invalid.
- Authorization evaluates the **principal's** relationships, then intersects
  with the delegation's scopes. An agent acting for an admin does **not**
  inherit the admin override.
- The authenticated principal object carries `is_obo` and `agent_id`; every
  delegated action is audited with both identities.
- Browser-side tools follow the same shape: metadata by default, privileged
  content requires a human confirmation each time, excluded material is never
  readable through tools, and deleting, sending or sharing are never tools.

## 8. L6 — Consent

- A `ConsentRecord` is immutable and append-only: scopes, purpose, exact
  displayed text, policy version, timestamp, user agent, third parties
  disclosed. Withdrawal, re-consent after a material policy change, and purpose
  expansion are **new records**; the ledger is the proof.
- The repository port has `append` and `list_by_user` only. No update, no
  delete.
- Heightened-sensitivity scopes (financial, health, protected-party data)
  gate the corresponding features.
- Consent precedes collection: write use cases that persist personal
  information verify an active consent record first and raise a typed
  exception otherwise; the UI reflects the gate, it does not implement it.

## 9. L7 — Encryption and erasure

- **Envelope encryption**: a master key-encryption key held only by the
  `KeyManagementPort` adapter wraps per-tenant data keys; especially sensitive
  fields use per-user keys wrapped by the tenant key. A single platform-wide
  HMAC key serves blind indexes for exact-match lookups that must work before
  the tenant is known (login by email).
- Every encrypted value is a self-describing envelope: version, `key_id`,
  nonce, AES-256-GCM ciphertext + tag, with the header bound as associated
  data. **The envelope's `key_id` is authoritative on read**, so rotation is
  lazy and old rows keep decrypting.
- `KeyManagementPort` is the sole boundary to key material: no call site
  outside its adapters touches a KMS SDK, the crypto library, or a key file.
  It lives in the application layer; the codec and adapters live in
  infrastructure; the domain never imports it.
- Encryption is absorbed at the ORM boundary by column type decorators;
  repositories, use cases and controllers are unaware. Unwrapped keys live
  only in a request-scoped cache, never persisted, never logged.
- **Crypto-erasure**: destroying a data key makes everything under it
  permanently unrecoverable (the deletion primitive for right-to-be-forgotten
  and tenant deletion). Destruction overwrites the wrapped key bytes, writes
  an append-only destruction record, and subsequent reads raise a distinct
  `KeyUnavailableError`, not an integrity error.
- Tamper or wrong key always surfaces as an integrity error, never garbage
  plaintext.
- Migrate the highest-blast-radius table (users/login) first and alone; then
  the same recipe per table with no permanent dual-read branch.
- A local keyring adapter serves dev/CI; the cloud KMS adapter is selected by
  config at the composition root.

## 10. L8 — Audit and evidence

- Two trails, deliberately separate: the general application audit log, and
  a structured **authorization audit** (`authorization_decision`,
  `relationship_change`, `delegated_action`) with actor, resource, action,
  decision, relationship, agent and principal. Both are append-only.
- Breach records, correction requests, and compliance gates are their own
  small aggregates with their own lifecycle and retention floor, not rows in
  the general log where a pruning job could sweep them.
- Every mutating verb in a dual-audience (human + AI) system has a `simulate_`
  dry-run sibling and produces an audit record with actor, actor type, reason
  and timestamp. An agent may answer and propose; consequential changes
  require a human authority record.
- Evidence export is a read-only packager: it reads the audit log, CI
  summaries, the classification registry and breach records into a dated
  bundle; it never writes to what it reads.
- Governance documents (runbooks, control mappings, residency decisions)
  live in one `compliance/` root with "last reviewed / next review due"
  metadata; public-facing subsets are linked from a trust page, the rest from
  nowhere public.
- An audit middleware that never wrote anything is a silent compliance
  failure: test that the audit path writes, end to end, through the real app.

## 11. Data-minimisation rules

Privacy rules include what is **left out**, not only what is protected:

- Protected parties (minors, dependants, non-party individuals): never
  solicit statements from them to gather evidence; record unprompted
  statements the same day in exact words; leave out other people's health
  information, other household members, and informants.
- Roles decide: the responsible professional decides what is produced or
  disclosed; the client decides what is sent. Tools never send, draft, reply
  or forward on anyone's behalf.
- Verify before use: every claim is labelled verified / client's account /
  contradicted / not found, with a citation.

## 12. Tests that prove the layering

| Layer | Test |
|---|---|
| L0 | repo scan for secrets and private paths; index shrink guard test; custody chain verify |
| L1 | classification coverage audit script, gated once green |
| L2 | classification unit tests per role combination; generated views and exports contain no privileged rows outside the privileged audience; server audience-scope test |
| L3 | ownership invariant over every aggregate; role matrix; endpoint mechanism ledger |
| L4 | authorization service tests per relationship and action; repository scoping tests |
| L5 | delegation scope intersection; admin override not inherited; audit entry written |
| L6 | ledger append-only (no update/delete on the port); withdrawal creates a new record; consent gate raises before any write |
| L7 | envelope round-trip, tamper detection, wrong key, destroyed key → unavailable; rotation reads old rows; blind index lookup |
| L8 | audit trail written through the real app; breach record retention floor; evidence bundle verifies by hash |
