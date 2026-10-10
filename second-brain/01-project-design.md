# Second-brain project design rules

Source: a private evidence-management workspace (a code repo with skills, a
record repo, a derived index), its handbook, playbook, model and bundle
contracts, and a fact-layer design (Karpathy's LLM-Wiki made strict). These rules generalise that setup to any project whose value is a
verified, citable record built from scattered sources.

## 1. Three folders, four tiers

```
<project>-tools/                 one workspace root (private; never shared as a whole)
├── <code>/        code and skills: collectors, index, model, scripts, .claude/skills   git, private, NO real data
├── <record>/      the record: originals by hash, configs, working notes, vaults      git + LFS, private
└── <index>/       derived: search index, model DB, manifests, history                 not in git; rebuildable
~/<project>-private/   local only: raw databases, ad-hoc exports                       never synced, never git
~/.config/<project>/.env   secrets                                                     never printed, never git
```

- **Code here, data elsewhere.** The code repo's fixtures are fictional; a
  clone of it exposes nothing. The record repo needs no code to be read.
- A root `CLAUDE.md` names the layout, the hard rules, where current state
  lives, and how to work. Each sub-repo has its own `CLAUDE.md` deferring to
  the root.
- Both repos work on the same branch name per session; commit messages carry
  the session attribution trailers; one commit per topic.

## 2. Sources are read-only; originals are write-once

- Collectors read mailboxes, chat databases, drives and exports; they never
  send, draft, label, move, delete, or write back. The user sends everything
  themselves.
- Every original is stored by SHA-256 with a hash-chained custody log
  (`custody.jsonl`) and a `SHA256SUMS` per folder; `sha256sum -c` is the
  verify step. A failed verify stops the cycle for that source.
- A connector-derived index (bodies without raw bytes or headers) is **index,
  not evidence**; say so in a `PROVENANCE.md` with the collection date, tool,
  caveats, and known sensitive content. Evidence-grade archives come from
  code-driven collection with raw bytes.
- Large originals are tracked through LFS; pushes run in the background.
- Derived builders refuse to run when an input no longer matches its recorded
  hash, and produce byte-identical output for the same inputs.

## 3. One fixed schema, one vocabulary, one classifier

- The record model has a versioned contract (`<model>/<major>.<minor>`):
  tables, columns, note types, folders, frontmatter, sections, enum values.
  Machine schemas are generated from one vocabulary module and checked for
  drift in tests.
- **Never invent** a field, folder, note type, heading or enum value in an
  output. To extend: change the vocabulary, bump the version (minor =
  additive, major = changed/removed), add a change-log line, regenerate the
  schemas, update tests, rebuild. Validators treat unknown anything as an
  error, and builders validate their own output before replacing anything.
- Audience and privilege logic lives in **one module**; the index, the model,
  the vault and the export call it. Nothing re-implements it. Roles that are
  not explicitly mapped stay `unknown` and are listed as unmapped; they are
  never guessed.
- No names, paths, chat ids, or domains in code: who is who comes from
  `people.json` and the profile; sources from a sources config; record knobs
  from one record-config file.

## 4. Generated versus owned content

```
record/vaults/<audience>/generated/   rebuilt by code every time; committed so a fresh clone opens
record/vaults/<audience>/notes/       yours; never touched by the generator; committed and versioned
```

- The generator replaces `generated/` only after confirming every file there
  carries its `generated: true` marker; a hand-edited file aborts the build
  and is listed, so you move it to `notes/` first.
- One vault per audience, each complete and self-contained; a combined `all`
  vault for the owner only. Audience is enforced per vault: an issue note shows
  only the steps that audience holds and is omitted when fewer than two remain.
- Every generated note links to the exact source block (message id anchors),
  so a claim can point at one message.
- Pages render from rows; synthesis lives in the compiled `wiki/` (§4a);
  free human prose lives only in `notes/`.

## 4a. The compiled wiki

Between the rows and the human notes sits a third tier, the part of the
LLM-Wiki pattern that the rows alone do not give: condensed, interlinked
concept pages that the model maintains and code renders.

```
record/vaults/<audience>/generated/   rendered from rows, one page per row kind
record/vaults/<audience>/wiki/        compiled by the LLM from rows and items; generated: true
record/vaults/<audience>/notes/       human prose; never touched by the generator
```

- A wiki page is a concept, entity, topic or question, written by the model
  from the rows and items it cites. Every page carries `generated: true`,
  `compiled_from` (the row ids and item ids it was compiled from, with their
  hashes) and `compiled_at`; a page with no `compiled_from` fails the build.
- **The LLM proposes; code records and renders** holds here too: the model
  writes a compile proposal (new or changed pages, as a patch); code
  validates the frontmatter, checks every link and citation, applies it,
  and logs one `compile` op (§11). The model never writes into the vault.
- Each ingest ends with a compile pass: the pages whose `compiled_from`
  overlaps the new items are recompiled, the **index page** (`wiki/index.md`)
  is regenerated, and pages that link to a recompiled page are touched in
  the same pass so their summaries do not go stale.
- The index page lists every wiki page and every `notes/` page with inbound
  and outbound link counts; it is regenerated per compile, never edited.
- Links and citations are validated in the same build that validates the
  vaults: a dangling wiki link, a citation whose item hash is unknown, an
  orphan page (no inbound link and not the index) or an orphan note fails
  the build and is listed.
- A wiki page is a reading of the record, not the record: a disagreement
  between a page and a fact row is a lint finding (§11) and the row wins
  until the page is recompiled.

## 5. The fact registry and the gap log

- `data/facts/facts.jsonl` is append-only: `key`, `value`, `unit`, `verdict`,
  `asserted_by`, `sources[]` (evidence by hash + locator + quote), `method`,
  `recorded`, `supersedes`, and optional rule/variable links. Derived numbers
  record `script@commit` and input hashes.
- **The verdict enum is defined here and only here**; `01` §6, `03` §7 and
  `04` §4 cite it:

  ```
  verdict ∈ { verified,       quote and citation in the record
              owner_account,  the record owner's statement, not yet corroborated; what would prove it is noted
              contradicted,   the record says otherwise; the quote is cited and dropping the claim is recommended
              partial,        part of the claim is verified; the rest is owner_account or not_found
              not_found }     searched and absent; the sources and queries tried are named
  ```

  Check: the vocabulary module is the single source of this enum; a test
  fails on any other literal list of verdict values in code or rules.
- `asserted_by` names who put the claim forward. Its values are **profile
  configuration** (`03` §14); the neutral defaults every profile starts from
  are `participant | counterparty | professional | authority | document`.
- Each key number is stored **once**; documents reference `{{fact:key}}` and
  rendering fills it. This is what prevents the same figure drifting across
  files.
- Check the registry before quoting a number; append before writing a new or
  corrected fact anywhere else.
- **Corrections supersede visibly**: a new row with `supersedes`; rendered
  pages show the old value struck through with the dated correction. Never
  silently rewrite.
- `data/facts/gaps.jsonl` records every unanswered question with what was
  searched (source, query, date, result) and what to try next. "Not found"
  must name the places searched. Work the gap log down before asking the
  person.
- A missing-items tracker holds open items with priority, reason, and a
  `detect` regex so an arriving file can close the item automatically.

## 6. Verify before use

For every claim the person makes that will be relied on:

1. Search for it **and against it**: a counterparty's own words, earlier
   dates, the person's own messages the same day.
2. Label it with one verdict from the enum in §5, with the quote and
   citation that justify it.
3. Correct the record kindly and early, before it reaches anyone else.
4. Re-date "origins": the first hit is usually a late instance; search older
   sources before writing "first appears".
5. Record what cuts against, in its own section.

Weight: contemporaneous record > later recollection > second-hand account; a
participant's own written words > a representative's summary of them.
Recollections go in a separate table.

## 7. Search, not grep

- A text index (FTS5 with optional local embeddings) over every source via
  adapters, one adapter per source type with a fixture test and a `source-*`
  skill.
- Token discipline: `count` → facet → `search` → `show --grep`, never opening
  whole files. Every hit prints a citation that the original can reproduce.
- A read-only MCP server exposes the index to AI sessions; databases open
  `mode=ro`; a server can be pinned to one audience in its config, and several
  copies under different names make scope a choice of server.
- Rebuilds are non-destructive: built in a temp dir, swapped in, the previous
  index kept in `history/` (newest N), and a shrink guard refuses a smaller
  index without an explicit flag. A `MANIFEST.json` records counts and input
  hashes.
- **File the answer.** A search that answers a question does not end at
  `show`: an answered question becomes a cited wiki page (§4a) or an update
  to the page that should have answered it; an unanswered one becomes a
  `gaps.jsonl` row with the sources and queries tried. Either way one
  `query` op is appended to `log.md` (§11) naming the question, the hits
  and the page or gap it produced. Check: every `query` op links to a page
  or a gap id; a lint lists questions in the log with neither.

## 8. The review cycle

One cycle = **status → collect → verify → index → compile → lint → review →
record → hand off**. Config lives in the record repo
(`data/review_cycle.json`: repos, index, trackers, deadlines, logs); the
skill holds no record facts.

- **Status first, read-only**: deadlines within 21 days (flagged at 7),
  uncommitted or unpushed work, index sources whose files changed, open
  tracker items by priority, logs not updated in 7 days. Tell the person the
  top three.
- Collect by source with the matching skill; verify each touched archive;
  re-index; compile the wiki pages the new items touch (§4a); run lint (§11)
  and clear or record its findings before review; review and classify every
  new item and claim; update existing registers rather than starting new
  files; supersede visibly.
- Record: close tracker items, add deadlines, write meeting briefs (facts,
  open decisions for the professional, what the person owes), commit per
  topic.
- Hand off with a short summary: what changed, what was corrected, what is
  due next and who owns it, what is half-done.

Quality gates before anything leaves the record: every fact has a
reproducible citation; no privileged content in any output for an audience
that does not hold it; account numbers masked; the profile's excluded
categories absent; produced artifacts are rendered from raw originals; the
accountable professionals have made their calls, the reviewer has not made
them for them.

## 9. Handoff and state

- `working/<me>/HANDOFF.md` is the **record workspace's** single live-state
  document: people (don't mix them up), deadlines, each live workstream, open
  items with owners, tools built, notes for the assistant, dated updates
  appended at the bottom, and a "do this first next session" section when
  something is broken. The build brain's equivalent is `progress.md`
  (`specs/05` §3); one brain, one live-state file (`shared/14` §3), and a
  test fails a project with two.
- There is no separate handover log: what happened in a session is the run
  of `log.md` rows between two hand-offs (§11); same-day notes in exact
  words go to `notes/` and are cited from the log row.
- A new person starts with the handbook, then status, then the profile and
  urgent tracker items, then the latest privileged notes for the deadline
  list, then asks what changed.
- Deadlines are config, not prose, so status can compute them.

## 10. Audience-scoped outputs and exports

- Working notes: privileged analysis under `working/<me>/_PRIVILEGED/`, first
  line marking it as prepared for the accountable professional; shareable
  fact lists elsewhere.
- Exports are write-once bundles: refuse an existing output dir, refuse to
  write inside the record, build in a sibling temp dir, rename into place,
  leave files read-only, hash every part in a manifest, re-verify by hash.
  Privileged rows are withheld by default with counts only; a claim citing a
  withheld row keeps the claim and drops the pointer. Same inputs give the
  same bytes.
- Ids are opaque, stable, derived from identity (message id, document hash +
  page), so re-export yields the same ids and duplicates across archives
  collapse to one.
- Bundle versioning: minor adds optional fields and importers ignore unknown
  properties; major changes or removes.

## 11. AI in the loop

- **The LLM proposes; code records and renders.** Model output is a patch
  that the tooling validates, applies and logs. **The human is editor, not
  author**: people approve and correct; code and the model draft. A human
  edits a row or a page only through a `correct` or `curate` op, never in
  place.
- **Lint** is a cycle stage (§8), between compile and review. The
  deterministic pass runs first and fails the stage on: conflicting values
  for a key, quotes no longer present in the source, tracker items whose
  detect pattern already matches, superseded facts still quoted, stale pages,
  uncited originals, timeline contradictions, orphan `wiki/` or `notes/`
  pages, broken wiki links, concepts cited in fact rows that have no wiki
  page, and curation rows whose cited items are superseded (below). The LLM
  pass runs second and only proposes: its findings and next questions are
  written as `gaps.jsonl` rows (`what to try next`), never as prose or page
  edits. Check: lint is a command with an exit code; the cycle driver refuses
  to advance to review while it fails.
- **Curation cites its evidence.** Every curation or override row (merged
  topics, renamed episodes, dropped candidates, binding overrides) carries
  the item ids that justified it and a `recorded` date; a row without them
  is rejected. Lint marks a row stale when a cited item is superseded or its
  hash is no longer in the record and lists it in the hand-off; a stale row
  still applies until a person re-curates or drops it. Every curation write
  is a `curate` op in the log with the principal who made it (`shared/08`
  §6). Test: a fixture row with no citation fails validation; superseding a
  cited item makes the next lint report the row stale.
- **One log per brain.** `log.md` is the rendered view of the hash-chained
  event log (`## [date] op | title`, one row per op) and the only narrative
  of what the tooling and the model did. The op vocabulary is closed:

  ```
  op ∈ { ingest, compile, query, lint, verify, correct, render, export, curate }
  ```

  Custody entries, audit entries and run records feed rows into this chain;
  they are not separate stories, and a project with a second running log
  fails the layout test. Check: the log schema's op enum equals this list;
  a test asserts every op in the enum appears in the fixture log and no
  other op does.
- Skills are per source (acquire → curate → index → review) and per method
  (search, review, cycle, produce). A skill states what it never does
  (send, draft, contact a protected participant, read a keychain without the
  key) before what it does.
- Be upfront about where the model runs and what it will read; privileged
  material may need the accountable professional's say-so before an AI
  session opens it.
- Browser-agent tools, if any, are metadata by default, gate privileged
  content on a human confirmation each time, and never expose delete, send,
  share or export-privileged as tools.

## 12. Integration with rule systems

When the second brain feeds a rules-driven product: facts link to stable
rule and form identifiers (URNs) and to published rule variables, never to
unstable question ids or low-confidence bridges; record objects get their own
URNs (`urn:<record>:<id>:fact:<key>`); evidence is `urn:sha256:<hex>`; the
consumer resolves URN → id through one resolver.

## 13. Starting a new second-brain project

1. Scaffold from a template (`init <folder> --me <name>`): `data/people.json`,
   `profiles/`, `data/review_cycle.json`, `data/<document-index>_sources.json`,
   `data/<record-config>.json`, `data/facts/`, `working/<me>/HANDOFF.md`,
   `vaults/` (with `wiki/` and `log.md`).
2. Fill in who is who (the roster roles the profile marks privileged) before
   collecting anything.
3. Start the slow exports on day 0; collect email first; add a named gap query
   whenever a question comes up.
4. Index, build the model, generate vaults, validate.
5. Check your own story against the record before anyone else sees it.
6. Run the review cycle every session; hand off at the end of each.
