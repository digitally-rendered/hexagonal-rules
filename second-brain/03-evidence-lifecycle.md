# The evidence lifecycle: ingest, notarize, store, classify, index, search, review, tag, produce

`01-project-design.md` describes the workspace and the session cycle. This
file is the **item-level** lifecycle every piece of collected material goes
through, and the defensibility rules that make the record usable in front
of a court, a regulator, an auditor or a counterparty: what proves an item
is unaltered, how every derived value traces back to an original, and how
inputs, tools and access are tracked. Source: the collectors, exhibit
renderer, custody logs, catalogues and skills of a private evidence
workspace; generalised.

## 1. The lifecycle

```
acquire   → read-only pull from the source system, by code
notarize  → SHA-256 of the exact bytes; append a hash-chained custody entry; record the run
store     → write-once object by hash (link, 0444); derived output only in new run directories
extract   → text layer, OCR, headers, attachments, reply graph; a manifest hashing every output
classify  → who is on it → audience and privilege; kind; dates with their source and precision
index     → search chunks with citations; the record model; rebuilt non-destructively
search    → count → facet → search → show; every hit cites a locator the original reproduces
review    → verify each claim for and against the record; label; record what cuts against
tag       → topics by keyword rule (navigation, never findings); issues and curation by hand
produce   → exhibits rendered from raw bytes with embedded source and manifest; verify; redact on a copy
retire    → nothing is deleted; superseded items and corrections are new entries that point back
```

Each stage is a command with an exit code; `verify` runs after any touched
archive and a failure stops the cycle for that source.

## 2. Acquire

- **Read-only against the source**: mailboxes opened in examine mode and
  fetched with peek so read state never changes; file sources only opened for
  reading; app exports requested by the person; browser captures printed
  from the public page. Mutating operations (store, copy, move, expunge,
  delete, send) are blocked in code, not by convention.
- **By code, not by hand or through an AI connector**: a connector-derived
  index (bodies without raw bytes or headers) is **index, not evidence**; it
  is used to cross-check the code-driven archive, never as an exhibit, and its
  provenance file says so.
- Every acquisition records: source system, account, folder, source ids
  (UID and validity, platform message and thread ids, labels), server
  receive time, fetcher and version, the query that matched it, the
  machine, and the run id.
- Incremental re-collection skips ids already acquired; identical bytes are
  logged as a new acquisition but stored once; differing bytes for the same
  logical message are flagged.
- Secrets come from the environment or a prompt; they never enter the
  archive or a custody log.

## 3. Notarize and store

- **Content addressing**: the object name is the SHA-256 of the exact bytes
  as delivered; nothing is normalised before hashing.
- **Write-once**: publish with a link operation that cannot replace an
  existing file; set read-only; there is no delete path. Git keeps the hash,
  not the mode, so after a clone the hash is the proof and the mode is
  restored by hand.
- **Custody log**: an append-only JSONL where each entry commits to the
  previous:

  ```
  {seq, prev_hash, entry_hash, event, payload, recorded_at, run_id}
  ```

  Events: run start (machine, collector version, source, queries), each
  acquisition (hash, size, locators, metadata such as PDF info or EXIF),
  each parse run (input hashes, output hashes), each verification. Errors
  are logged, never dropped.
- **Per-folder `SHA256SUMS`** for curated exhibit folders and originals;
  `sha256sum -c` is the check.
- **Manifests**: every derived directory carries a manifest with tool
  versions, input hashes, output hashes and counts; the manifest's own hash
  is written to the custody log.
- **Verify**: re-hash every object and replay the custody chain; any
  edited, removed or reordered line is reported; exit code non-zero.
- Large originals are tracked through LFS in the private record; exports too
  large for the host stay with the person's originals and are listed by
  hash.
- **Optional timestamping**: a trusted timestamp (RFC 3161) or a public
  anchor can wrap the manifest or the custody head to prove existence at a
  time; it adds to, and never replaces, the hash chain.

## 4. Extract

- Text layer first, OCR for image-only pages and scans, one page break per
  page; inventory rows carry hash, pages, method and the text file.
- Email: headers as sent, body text and HTML (rendered offline, scripts
  disabled, no network), attachments decoded into the same content-addressed
  store, reply graph from `Message-ID`, `In-Reply-To` and `References` with
  the platform thread id kept alongside; replies to messages not in the
  archive become a **missing-parents list**, which is the list of things to
  go and find.
- Platform reports (co-parenting apps, bank statements, court e-filing
  stamps) are **not re-rendered**: the original file is the evidence; parsed
  JSON is a convenience copy and every parsed row carries `report, page,
  line` back into the original.
- Duplicate copies of one logical message (inbox, sent, export) collapse to
  one logical item listing every raw copy.
- **Corroboration** between independent sources (platform report versus
  notification emails, document versus the message that carried it) is a
  recorded cross-check with matched and unmatched lists, not an assumption.

## 5. Classify

- **Audience and privilege** from who is on the item, by the one classifier
  (`shared/08` §4). Catalogued documents may carry an explicit audience; the
  most restrictive explicit audience wins.
- **Kind** (email, platform message, text, document, page, ledger row,
  journal entry) from one vocabulary.
- **Dates with provenance**: content date (signature, letterhead, filing
  stamp) outranks file-name date outranks file-system or PDF creation time;
  the date's source and precision are recorded and flagged in reports.
- **Executed versus draft** is catalogued for agreements and orders; a draft
  shows negotiation history, not terms.
- **Sensitive content** (card numbers, identity numbers, protected-party
  details) is flagged in the inventory or provenance and kept unedited in the
  original; redaction happens on produced copies only.
- The catalogue (`title, date, category, audience, sensitive, described_by`)
  is the one hand-edited file in an archive; originals are never renamed.

## 6. Index and search

- Search chunks per item or page with a locator (`original path + page`,
  `report + message + page`, `chat id + row`, `raw sha256`); the record
  model joins chunks to items through evidence references.
- Non-destructive rebuilds: temp directory, swap, previous copy kept in
  history, shrink guard, manifest of counts and input hashes.
- Search, not grep; every hit prints a citation the original reproduces;
  quote from the original when it matters.
- Servers are read-only and audience-scoped; a connector session sees only
  the audience it was opened for.

## 7. Review

- Every claim that will be relied on is searched **for and against**,
  labelled (verified / client's account / contradicted / partial / not
  found), and corrected early and visibly. "Not found" names the sources
  and queries tried; an exhausted search trail is itself evidence of
  absence.
- Weight: contemporaneous record > later recollection > hearsay; a party's
  own sworn or written words > their advisor's submissions.
- Professional reports are recorded as written (author, credentials, dates,
  instruments, findings) before any party's description of them is compared.
- Review outputs are cited rows (date, actor, issue, quote, source, locator,
  label) plus reasoning; one claim per row; ellipses marked.
- Facts and gaps go to the registries (`01` §5); corrections supersede.

## 8. Tag and curate

- **Topic tags** are keyword rules over an item's own text (quoted history
  excluded); they are a navigation aid, every tagged note says so, and they
  are never findings.
- **Issues and episodes** come from analysis output and are curated by hand
  (merge, rename, drop, annotate) in a curation file that rebuilds apply
  every time.
- **Exhibit sets** are declared, not assembled by hand: name, label, date
  window, subject patterns, excluded participants (the user's own advisors
  are excluded automatically and counted); preparing an exhibit is not
  producing it.
- **Trackers** of missing items carry priority, reason and a detect pattern;
  arrival closes the item automatically.

## 9. Produce

- Exhibits are rendered from **raw bytes**, never from parsed or re-typed
  text. Anatomy: full header block (as sent and in UTC, message and reply
  ids); a provenance box (source hash, archive object, custody sequence and
  entry hash); the body; an attachments table with hashes and renderable
  attachments appended; a footer on every page (Bates number, exhibit label,
  page x of y, source hash); the original embedded as a file attachment; a
  sidecar manifest (source hashes, custody entry, renderer and browser
  versions, exhibit hash). Bates numbers continue across exhibits from the
  previous manifest.
- `verify-exhibit` checks embedded source ↔ PDF metadata ↔ manifest ↔
  bytes, and can extract the original back out.
- Rendering is not byte-reproducible; sources are. A regenerated exhibit
  has a new hash and the same source hashes; always produce the manifest.
- **Redact only on a copy**, keep the unredacted exhibit, remove the embedded
  original from the redacted copy (it would no longer verify) and say so in
  the cover note.
- Bundles for an external consumer are write-once, hashed per part,
  withhold privileged rows by default with counts only, and verify by hash
  (`01` §10).
- Real exhibits never live under a code repository.

## 10. What proves what

| Source | Produced | Proof of integrity |
|---|---|---|
| email collected by code | exhibit PDF | raw object hash + custody entry (account, folder, uid, time) + embedded original |
| email saved by a person | exhibit PDF | hash of the saved file + embedded original; weaker custody (who saved it, when) |
| platform report | the file as downloaded | platform-generated sequence and receipts; file hash; cited by page and line; the platform's own records are the check |
| chat exports | the export file | hash + collection notes (device, app version, date); cited by row or pointer |
| photos, scans, screenshots | the original file | hash, metadata where present, date source and precision flagged |
| connector-derived index | nothing | index only; cross-check target, never an exhibit |

## 11. Tracking inputs, tools and access

- **Inputs**: every run names its inputs by hash (sources, configs, prior
  derived outputs); rebuilds refuse to run when an input no longer matches
  its recorded hash; the same inputs produce byte-identical derived output.
- **Tools**: collector, parser, extractor, renderer and browser versions are
  in every manifest; derived numbers record `script@commit` and input hashes.
- **Decisions and corrections**: facts and gaps are append-only with
  `supersedes`; working notes strike the old statement and date the
  correction; handoff logs are dated.
- **Access and actions**: an event log (ingest, verify, correct, lint,
  render, export) as a hash chain rendered as a readable log; connector and
  tool-server calls audited with actor type (human or agent), tool, inputs
  and session; privileged content requires a human confirmation each time it
  is opened through a tool.
- **People and roles** live in one roster; an unmapped correspondent stays
  unknown and listed; nothing is guessed.
- **Delegated roles**: the advising professional decides production and
  disclosure, the client decides what is sent, the reviewer documents and
  verifies; tools never send, draft, reply or forward.

## 12. What AI may and may not do here

- May: propose catalogue descriptions (marked as drafted and to be checked),
  propose topics and issues, draft review notes with citations, run searches,
  classify through the one classifier, propose facts and corrections as
  rows for validation.
- May not: alter an original, rename an original, decide audience by
  keyword, send or draft outbound communication, open privileged material
  through a tool without a human confirmation, or treat a connector preview
  as a source.
- Say up front where the model runs and what it will read.

## 13. Tests and gates

| Concern | Check |
|---|---|
| originals unchanged | `verify` re-hashes objects and replays the chain; `sha256sum -c` per folder |
| nothing written to sources | collectors have no mutating code path; a test asserts the blocked operations |
| derived reproducibility | rebuild twice, diff manifests |
| classification | unit tests per role combination; produced sets contain no excluded participants |
| exhibits | `verify-exhibit` on every produced file; Bates continuity across a set |
| registries | facts and gaps append-only; a lint flags conflicting values, quotes absent from source, superseded facts still quoted |
| missing items | tracker detect patterns run on every ingest |
| audience scope | the read-only server refuses out-of-scope items for every tool |
