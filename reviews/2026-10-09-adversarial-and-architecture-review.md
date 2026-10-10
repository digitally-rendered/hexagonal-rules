# Review record: adversarial (knowledge-system lens) and architectural, 2026-10-09

Two independent reviews of this repository at commit `50421bd`, run by
separate agents with no shared context, then verified line by line before
remediation. The first used the LLM-wiki second-brain pattern and the
unattended-research loop as its lens; the second reviewed architectural
soundness, cross-reference integrity, one-authority-per-fact, the repo's own
MUST-names-a-check standard, layering of the rules repository itself, and
sourcing compliance. Findings are summarised here without quoting any
private content that was found and removed. Remediation follows the repo's
own classes (`specs/05` §2): A, the rule was wrong and is corrected; B, the
rule was ahead of reality and is marked as design; C, the rule and the
sources disagree and the disagreement is recorded.

## Totals

| Severity | Lens review | Architecture review | Fixed | Recorded as dissent (C) | Open |
|---|---|---|---|---|---|
| blocker | 3 | 4 | 7 | 2 of the 7 also recorded in `shared/05` | 0 |
| major | 13 | 19 | 32 | — | 0 |
| minor | 8 | 17 | 25 | — | 0 |

## Blockers and what changed

| Finding | Class | Change |
|---|---|---|
| The reindex hook never read its input, so it never ran; the whole index-freshness story rested on it | A | `templates/gitnexus-reindex-hook.sh` captures stdin before invoking the parser; `templates/test-reindex-hook.sh` runs seven cases with a stub binary in CI |
| Domain content and identifiers from private sources sat in `shared/08`, `second-brain/01`, `shared/09`, several language files and a template, against `CLAUDE.md` | A | mechanism kept, domain vocabulary moved to the adversarial profile row of `second-brain/03` §14 in neutral terms; identifiers replaced by placeholders; placeholders in templates; an optional private-term scan added to the repo lint |
| The Go rung ran custom validators before schema validation and dropped hooks from its pipeline, reversing the resolution recorded in `shared/05` | A + C | `go/01` §5 states the shared order and names the lifecycle-order test; `shared/05` records that the Go framework currently dissents, dated |
| The Python rung turned a failing post-hook into a 500, reversing the recorded resolution | A + C | `python/02` §11 states logged-and-response-unchanged with its test; `shared/05` records the dated dissent |
| No compile step: the second brain rendered rows and kept prose in notes, so no maintained wiki of condensed, linked pages existed | A | `second-brain/01` §4a adds the compiled `wiki/` tier with `compiled_from` citations, an index page, related-page touch and link validation; `compile` is a cycle stage |
| Answers were never filed back, so the system did not compound | A | "file the answer" in `second-brain/01` §7 with a `query` log op; the operation brain's discard of working memory is stated as a privacy trade-off in `shared/14` §4 |
| Six logs with two op vocabularies and no single append-only narrative | A | one `log.md` per brain with a closed op enum rendered from the hash chain; custody, audit and run stores feed it |

## Major themes and what changed

- **One authority per fact.** Scope-specificity scoring now lives once in
  `shared/01` §6a; the pipeline is cited, not restated, in five places; the
  drift check per stack is one table in `shared/02` §1; the error table
  gained 503 and lost the per-language "plus" clauses; the single Class B
  test-skip exception is decided in `shared/04` §5; the verdict enum is
  defined once in `second-brain/01` §5.
- **Designs presented as facts.** The application MCP server, the
  simulate and explain siblings, generated screens and the frontend track
  are marked as designs with their status in `shared/13` §2a; `specs/02`
  rule 9 and `specs/03` rule 4 say "once the frontend track ships".
- **MUST without a check.** About twenty-five MUST lines gained a named
  check, one was downgraded to SHOULD, and `tools/check_rules.py` now fails
  CI when a section states MUST or NEVER with no check named.
- **Layering of the repo.** `shared/` no longer cites language folders or
  templates; the three-brains file moved to `shared/14` and the
  evidence-graded inputs file to `specs/06`, removing the cycle between
  `specs/` and `second-brain/`; the README lists `specs/` and the new files.
- **Restated source inventories.** The product roadmap, named hooks with
  language globs, skill and component inventories and runner flags were
  replaced by the principle and its check.
- **Lens gaps.** Lint is a cycle stage and hunts orphans, broken links and
  missing concepts; curation rows cite the items that justified them and go
  stale when those are superseded; a minimum profile is stated; the raw and
  compiled tiers are split for research inputs; `curator` and `editor` are
  roles.
- **Autonomy undefined.** `shared/15` defines autonomy levels per agent,
  brain and surface, the loop contract, promotion and demotion, and what the
  human reviews; the design agent has a column in `shared/14` §6.
- **Language parity.** `python/06` adds the privacy implementation; slice
  tests exist per language; the Go repository port records that it does not
  expose history yet.

## Still open after this pass

- The three dissents recorded in `shared/05` (Go validator order, Go hooks,
  Python post-hook status) are facts about the public frameworks today; the
  rules stand and the frameworks have backlog.
- `tools/check_rules.py` checks presence of a check word in a MUST section,
  not that the named check exists in a repository that adopts these rules;
  that remains the adopting repo's fitness-test job.
- The frontend track and the design system are designs with no shipped
  framework.

## Method notes

Two reviewers with disjoint lenses found the same blockers independently
(the hook, the privacy leakage, the brains' undefined autonomy), which is
the signal that they were real. Both reviews were verified against the
cited lines before any edit. Remediation was split between two agents with
strictly disjoint file ownership, and a final sweep applied the items each
owed to the other's files. The lint and the hook test ran green before the
commit.
