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
  from a `brain.json`.

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
- Pages render from rows; free prose lives only in `notes/`.

## 5. The fact registry and the gap log

- `data/facts/facts.jsonl` is append-only: `key`, `value`, `unit`, `verdict`
  (`verified | client_account | contradicted | not_found | partial`),
  `asserted_by` (`document | client | advisor | other_party | authority`), `sources[]` (evidence by hash + locator + quote), `method`,
  `recorded`, `supersedes`, and optional rule/variable links. Derived numbers
  record `script@commit` and input hashes.
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

1. Search for it **and against it**: the other party's words, earlier dates,
   the person's own messages the same day.
2. Label it: verified (quote + citation), client's account (what would prove
   it), contradicted (quote the record; recommend dropping it), partial.
3. Correct the record kindly and early, before it reaches anyone else.
4. Re-date "origins": the first hit is usually a late instance; search older
   sources before writing "first appears".
5. Record what cuts against, in its own section.

Weight: contemporaneous record > later recollection > hearsay; the other
party's own sworn words > their advisor's submissions. Recollections go in a
separate table.

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

## 8. The review cycle

One cycle = **status → collect → verify → index → review → record → hand
off**. Config lives in the record repo (`data/review_cycle.json`: repos,
index, trackers, deadlines, logs); the skill holds no record facts.

- **Status first, read-only**: deadlines within 21 days (flagged at 7),
  uncommitted or unpushed work, index sources whose files changed, open
  tracker items by priority, logs not updated in 7 days. Tell the person the
  top three.
- Collect by source with the matching skill; verify each touched archive;
  re-index; review and classify every new item and claim; update existing
  registers rather than starting new files; supersede visibly.
- Record: close tracker items, add deadlines, write meeting briefs (facts,
  open decisions for the professional, what the person owes), commit per
  topic.
- Hand off with a short summary: what changed, what was corrected, what is
  due next and who owns it, what is half-done.

Quality gates before anything leaves the record: every fact has a
reproducible citation; no privileged content in anything for the other side;
account numbers masked; excluded categories absent; exhibits are rendered
from raw originals; the professionals have made their calls, the reviewer has
not made them for them.

## 9. Handoff and state

- `working/<me>/HANDOFF.md` is the single live-state document: people (don't
  mix them up), deadlines, each live workstream, open items with owners, tools
  built, notes for the assistant, dated updates appended at the bottom, and a
  "do this first next session" section when something is broken.
- `handover_log.md` is the dated running log (same-day entries in exact words
  where it matters).
- A new person starts with the handbook, then status, then the profile and
  urgent tracker items, then the latest privileged notes for the deadline
  list, then asks what changed.
- Deadlines are config, not prose, so status can compute them.

## 10. Audience-scoped outputs and exports

- Working notes: privileged analysis under `working/<me>/_PRIVILEGED/`, first
  line marking it as prepared for the advisor; shareable fact lists elsewhere.
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
  that the tooling validates, applies and logs. Deterministic lint (conflicting
  values for a key, quotes no longer present in the source, tracker items
  whose detect pattern already matches, superseded facts still quoted, stale
  pages, uncited originals, timeline contradictions) runs first; an LLM pass
  only proposes findings.
- An event log of ingest / verify / correct / lint / render is a hash chain,
  rendered as `log.md` (`## [date] op | title`).
- Skills are per source (acquire → curate → index → review) and per method
  (search, review, cycle, exhibits). A skill states what it never does
  (send, draft, question a child, read a keychain without the key) before what
  it does.
- Be upfront about where the model runs and what it will read; privileged
  material may need the advisor's say-so before an AI session opens it.
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
   `profiles/`, `data/review_cycle.json`, `data/textindex_sources.json`,
   `data/brain.json`, `data/facts/`, `working/<me>/HANDOFF.md`, `vaults/`.
2. Fill in who is who (the own-advisor domain marks privileged items) before
   collecting anything.
3. Start the slow exports on day 0; collect email first; add a named gap query
   whenever a question comes up.
4. Index, build the model, generate vaults, validate.
5. Check your own story against the record before anyone else sees it.
6. Run the review cycle every session; hand off at the end of each.
