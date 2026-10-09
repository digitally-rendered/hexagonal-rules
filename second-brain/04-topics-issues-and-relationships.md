# Topics, issues and the relationships between content

The record is not a pile of items; it is a graph. This file defines the
node and edge types, their **cardinality**, the **temporal** and **logical**
tags every node and edge carries, how topics and issues are derived and
curated, and the rules for counting and reasoning across the whole set.
It is domain-neutral: the same graph describes a research corpus, a
product's history, a ledger or a dispute file; the vocabularies that differ
per domain (event classes, roles) are profile configuration (§9). The
mapping from text and fields to a domain model is in
`05-domain-mapping.md`. Everything here is **derived analysis, not
evidence**: every node and edge cites the items it came from, and the
originals remain the record (`03-evidence-lifecycle.md`).

## 1. Nodes

| Node | Identity | Cardinality notes |
|---|---|---|
| **Item** (message, platform message, text, document, page, ledger row, journal entry) | content hash or source locator | the atom; exactly one `kind`, one `audience`, one `privilege` |
| **Thread / conversation** | reply-graph root id (platform thread id kept alongside) | 1 thread : N items |
| **Attachment** | content hash | N attachments : M items (the same bytes may arrive in several messages; each occurrence is recorded) |
| **Person** | address or handle; aliases | 1 person : N identities; 1 person : 1 canonical role (unmapped stays `unknown`) |
| **Organization** | domain or name | 1 organization : N persons |
| **Day / Year** | calendar key | partitions items by time; every dated item is in exactly one day |
| **Topic (rule)** | name from the keyword rules file | N topics : M items (tags, not findings) |
| **Topic (discovered)** | stable key from topic discovery | N : M items; curated by name, merge or drop |
| **Issue / episode** | `<topic key>-<start date>` | one topic over one stretch of time; 1 episode : N items; an item may sit in several episodes (one per topic) |
| **Step** | episode + item + character offset | 1 step : 1 item; 1 episode : N steps; who did what, from a sentence |
| **Handoff** | episode + date | an issue moving channel or audience; 1 episode : N handoffs |
| **Project** | title | a dated log across sources; 1 project : N episodes |
| **Fact** | registry key (append-only chain) | 1 fact key : N rows over time, exactly one current row; 1 row : N sources |
| **Claim** | claim id | 1 claim : N evidence items; one verdict |
| **Gap** | gap id | 1 gap : 1 fact key or tracker id it would settle; N searches |
| **Produced artifact / set** | label; declared set | 1 set : N threads or items; 1 artifact : 1 rendered source plus embedded original |
| **Domain object** (party, account, product, project, …) | canonical id from the domain model (`05`) | N items : M objects via resolved mentions; one object per real-world thing |
| **External rule / requirement / schema field** | stable identifier (URN) | N rules : M facts; linked only through stable identifiers |

Every node carries `audience`, and the vault or server scope decides whether
it is visible; an episode with fewer than two visible items is omitted
from that audience.

## 2. Edges

| Edge | From → To | Cardinality | Derived by |
|---|---|---|---|
| `in_thread` | item → thread | N:1 | reply headers (authoritative), platform thread id (kept) |
| `replies_to` | item → item | N:1 (a missing parent is recorded as a to-find item) | headers |
| `carried` | message → attachment | N:M | decode; every occurrence listed |
| `same_bytes` | document → attachment / item | N:M | hash equality (`also_stored_as`) |
| `from`, `to`, `cc` | item → person | N:M with direction | headers |
| `member_of` | person → organization | N:1 | roster |
| `tagged` | item → topic | N:M | keyword rule or discovery; rule topics prefixed to tell them apart |
| `in_episode` | item → episode | N:M (one per topic) | topic + gap-day segmentation |
| `step_of` | step → episode, step → item, step → actor | N:1 each | subject–predicate–object extraction with resolved references (`05` §1) |
| `mentions` / `resolves_to` | item → mention → domain object | N:M, then N:1 | entity resolution through one resolver (`05` §2) |
| `handoff` | episode → (from item, to item) | 1:N per episode | audience or channel change between consecutive items |
| `linked_by_attachment` | item ↔ item | N:M | shared attachment hash across threads |
| `cites` | fact/claim → item (locator + quote + quote hash) | 1:N | review; required on every row |
| `supports` / `contradicts` / `cuts_against` | claim → item | N:M with polarity | review; both directions always searched |
| `corroborates` | item ↔ item | N:M | deterministic cross-check between independent sources |
| `supersedes` | fact row → fact row; note → note | 1:1 chain | append-only correction |
| `would_settle` | gap → fact key / tracker id | N:1 | gap log |
| `detects` | tracker item → item | 1:N | detect pattern on ingest |
| `in_set` | item or thread → produced set | N:M | declared set rules; excluded participants removed |
| `grounded_in` | fact/claim → rule URN | N:M | stable identifiers only; never a low-confidence bridge |

Rules: an edge is never inferred from keywords alone except `tagged`, which
is labelled as such; identity edges (`same_bytes`, `same_as` for people) come
from one resolver; every edge has at least one locator a person can open.

## 3. Temporal tags

Every item carries: `date_utc`, `date_local` (with the timezone used),
`date_precision ∈ {day, minute, instant}`, and `date_source ∈ {header,
platform, content, filename, filesystem, user}` in that order of authority.
A date whose source is weaker than `content` is a hint and is flagged in
any report that relies on it.

| Tag | Where | Use |
|---|---|---|
| day, month, year partitions | items | navigation, counts per window |
| `first_date`, `last_date`, duration | threads, episodes, projects | "how long has"; always re-dated by searching older sources before stating "first appears" |
| gap-day segmentation (default 21 quiet days) | episodes | one topic over one stretch of time; the parameter is in the manifest |
| sequence index | steps within an episode | order within a day; tie-break by item id and offset |
| `timeline_type ∈ {lifecycle, proceeding_step, deadline, communication, document, offer, mediation_stage, custom}` | timeline events | typed chronology for the bundle |
| deadlines and standing obligations | review-cycle config | computed status, flagged at 21 and 7 days |
| validity interval (`recorded`, `superseded_at`) | fact rows | which value was current when |
| delays | derived | request → refusal → reversal or adoption, in days; averages and worst cases reported with their population |
| relative relations | derived | `before`, `after`, `within N days of`, `during <episode>`; computed, never stored as prose |

Times from a platform are recorded in the platform's zone and converted;
the conversion is verified against an independent source (notification
emails versus report timestamps) before any delay is computed.

## 4. Logical tags

| Tag | Values | Carried by |
|---|---|---|
| event class | a **closed, per-profile vocabulary** of predicate classes; anything else is `other` and counted (§9 gives examples) | step |
| modifiers | negated, modal, question, instruction (a negated consent is a refusal; "can you…?" is a request) | step |
| actor resolution | explicit, from context (I/you/we from the header), `guess` (unresolved pronoun) | step; `guess` steps are kept in analysis but left out of notes |
| direction | `from`, `to`, `both` | item, step |
| audience, privilege, privilege basis | the one classifier | every node |
| verdict | `verified, client_account, contradicted, partial, not_found` | claim, fact |
| polarity | `supports, contradicts, cuts_against` | claim → item edge |
| status | `open, received, not_applicable, closed` | tracker, gap |
| final vs draft | catalogue | document |
| sensitivity | flag with reason | item |
| curation | `curated: true`, `curator_note`, merged-from ids | topic, episode |

Logical tags are either deterministic (headers, hashes, the classifier) or
**proposed** (topic discovery, sentence parsing, model descriptions) and
labelled as proposed; proposed tags change the record only through the
curation file or the review queue. Modality and defeasibility tags for
normative text (mandatory / discretionary / prohibited, exceptions,
priorities) belong to the logic-axis surface in `05` §7.

## 5. Topics and issues

- **Rule topics** are keyword regexes over the sender's own text (quoted
  history, signatures and forwards removed first, each cut listed). They
  are navigation; every tagged note says so.
- **Discovered topics** come from local topic modelling (candidate topics
  with top phrases and example items); a person names, merges or drops them
  in the curation file; rebuilds apply the curation every time.
- **Episodes** are one topic over one stretch of time across every channel
  and person: items ordered by date, split after the quiet gap, with steps,
  handoffs and attachment links. The episode note shows handoffs, steps
  (date, channel, actor, action, sentence, link to the exact block),
  messages, and items linked by a shared attachment; a canvas lays lanes per
  channel or audience for episodes that changed hands.
- **Projects** aggregate dated events across sources (mail, documents,
  ledger, code, design) into one log; events are sections per episode.
- Curation keys are stable (`topic key`, `episode id`), so curation survives
  rebuilds; a merged episode unions items, steps and handoffs and sorts them.
- Accuracy is measured before summaries are trusted: a random sample of
  parsed steps with a blank correct column is reviewed by a person and the
  rate recorded with the analysis manifest.

## 6. Cardinality for reasoning across the set

Counting is where derived analysis earns trust or loses it. Rules:

1. **Count symmetrically.** Every per-actor count of an event class is
   computed for every actor, and the same-class table is shown side by side,
   so a claim about one actor's behaviour is always read against every
   other actor's.
2. **Name the population and the denominator** for every number: the
   source set, the filters, the window, the exclusions, the count of items
   the number is over (`shared/06` §10).
3. **Aggregate, then cite.** Averages and worst cases link to the rows that
   produced them; a reader can open every contributing item.
4. **One item, one count per dimension.** An item is in exactly one day,
   one audience, one privilege, one kind; an item may be in many topics, so
   topic counts do not sum to the item count and tables say so.
5. **Precision propagates.** A delay computed from a day-precision date is a
   day-precision delay; mixed precisions are reported at the coarser one.
6. **Derived counts recompute.** Counts on notes (`request_count`,
   `handoff_count`, `thread_count`) are generated fields, never hand-edited;
   drift between a count and its rows is a build failure.
7. **Absence is counted too.** A "not found" with its search trail is a
   row; unmatched items in a cross-check are listed, not dropped; a count of
   withheld rows is reported with every produced set.
8. **Comparisons are same-schema.** Comparing two periods, two parties or
   two sources uses the same tags and windows; a change in a rule or a
   classifier version re-tags the whole set before any comparison.
9. **Queries live with the model.** The record database (SQLite with
   full-text search, optional vectors) answers the questions; note-level
   tables (live-query plugins or generated lists) are views of the same rows.
   Typical questions: how many events of a class per actor per month and
   how many were answered; the longest gap between a request and a reply;
   which issues changed hands most; which attachments appear in more than
   one thread; which domain objects are referenced across the most sources;
   which facts were corrected and when.

## 7. Model and schema

- Nodes, edges and tags are tables and columns in the record model and
  fields in note frontmatter, all drawn from the one vocabulary; validators
  reject unknown types, edges or values.
- Edge tables carry `source` (how the edge was derived), `confidence` where
  proposed, and `locator`.
- Extending the graph (a new node type, edge type or tag) follows the fixed
  schema rules of `01` §3: vocabulary, schema regeneration, version bump,
  change log, rebuild, validate.
- Export: the graph can be rendered as notes with wiki links and block ids
  (any editor; graph view and live tables with a plugin), as a canvas per
  episode, as JSONL parts of the bundle, and as a knowledge-graph file for
  external tools. Every export is generated; none is edited.

## 8. Tests

| Concern | Check |
|---|---|
| cardinality | every item has exactly one audience, privilege, kind, day; thread and episode counts equal their rows |
| temporal | dates carry source and precision; episodes are contiguous and non-overlapping per topic; delays recompute from rows |
| logical | action vocabulary closed; negated consent → refuse; `guess` steps excluded from notes |
| citations | every fact, claim, step and handoff resolves to an item locator |
| curation | merges and drops are idempotent across rebuilds; stable keys |
| audience | an episode shows only items the vault's audience holds; omitted when fewer than two |
| accuracy | a reviewed sample and its rate are recorded in the analysis manifest |
## 9. Profiles: per-domain vocabularies

The graph is fixed; the vocabularies that fill two of its columns are
profile configuration, drawn from the one vocabulary module and versioned:

| Profile | Event classes (steps) | Actor roles |
|---|---|---|
| communications / dispute | request, consent, refuse, inform, schedule, pay, cancel, propose, decide, accuse | owner, own advisor, other side, neutral professional, provider |
| product / engineering | propose, decide, implement, review, merge, release, revert, report | author, reviewer, owner, customer, vendor |
| research | claim, cite, support, contradict, replicate, retract | author, source, reviewer, editor |
| finance / operations | order, deliver, invoice, pay, refund, dispute, reconcile | buyer, seller, bank, auditor |

A step's class is one value from the active profile; cross-profile
analysis maps classes to the shared super-classes `ask, agree, decline,
inform, commit, undo, judge`.

