# Code intelligence and indexing (GitNexus, document index)

Every project on the ladder carries two indexes that agents and people
query through MCP instead of grepping: a **code graph** (symbols, calls,
imports, execution flows, API routes, cross-repo contracts) and a
**document index** (docs, specs, vaults, PDFs, generated artifacts). The
code graph is GitNexus. The document index is the project's text index
(the `textindex` pattern of `second-brain/01` §7) or Infigraph where it is
installed; both expose read-only MCP tools.

## 1. Why an index, and why it must be fresh

- A stale index gives wrong answers about callers, blast radius and
  affected flows. Treat staleness as a **correctness bug**, not a
  performance hint.
- Grep misses `import x as y`, re-exports, dynamic dispatch and strings;
  the graph is built from the AST and records relationships
  (`CALLS`, `IMPORTS`, `EXTENDS`, `IMPLEMENTS`, `DEFINES`, `MEMBER_OF`,
  `STEP_IN_PROCESS`) grouped into communities and execution processes.
- The index is keyed to a commit SHA. A branch switch, pull or merge almost
  always invalidates it.

## 2. Setup per project

1. **Install once per machine**: GitNexus as a global binary or via
   `npx gitnexus`; register it as a user-scope MCP server
   (`templates/mcp-servers.json`). Projects do not add it to their own
   `.mcp.json`; the global registry (`~/.gitnexus/registry.json`) routes
   requests by repo.
2. **Index the repo**: `npx gitnexus analyze` from the project root (add
   `--embeddings` when semantic search is wanted; multi-minute on large
   trees, run in the background). It writes `.gitnexus/` and the managed
   block in `CLAUDE.md` / `AGENTS.md`.
3. **Ignore the index**: `.gitnexus/` is in `.gitignore`; it is derived and
   rebuildable.
4. **Keep it fresh automatically**: a `PostToolUse` hook script re-runs
   `analyze` after git commands that move `HEAD` (commit, merge, checkout,
   switch, pull, rebase). The script parses the tool call as JSON on stdin
   and never evaluates the command text (`templates/settings-hooks.json`,
   `templates/gitnexus-reindex-hook.sh`).
5. **Allow the commands**: project settings pre-approve the exact
   `npx gitnexus status|analyze|list` commands and the read-only
   `mcp__gitnexus__*` tools (`templates/settings-permissions.json`). No
   wildcard after `npx` (its flags can run arbitrary commands behind an
   allowed prefix); `cypher`, `rename` and `group_sync` stay prompted.
6. **Add the skills**: copy the `gitnexus-*` skill family and
   `reindex-check` (`shared/11` §1) into `.claude/skills/`.
7. **Document index**: register the project's read-only text-index MCP
   server (or Infigraph) at project scope in `.mcp.json`, opened read-only,
   scoped to the audience the session may see (`shared/08` §4).
8. **Multi-repo products**: define a GitNexus **group** over the member
   repos (backend, frontends, shared packages, the second-brain record) so
   contracts (HTTP routes, topics, tool definitions) are cross-linked and
   `group_query`, `group_status`, `group_sync` and `group_contracts` work
   across the product.

## 3. The managed block in `CLAUDE.md`

`npx gitnexus analyze` rewrites everything between the
`<!-- gitnexus:start -->` and `<!-- gitnexus:end -->` markers. Never put
project notes inside the markers; put them above or below. The block states
the Always/Never rules below and the resource and skill tables
(`templates/claude-gitnexus-block.md` is the reference copy).

## 4. Rules

**Always**

- Run `reindex-check` (or `npx gitnexus status`) at session start before
  editing existing symbols, after pull/merge/checkout, after a commit that
  adds, removes or renames symbols, and before any multi-commit refactor.
  Cross-check the indexed SHA against `HEAD`; a fresh status with a
  diverged SHA is a FAIL.
- **Before editing any function, class or method**: `impact({target,
  direction: "upstream"})` and report direct callers, affected processes
  and risk level. HIGH or CRITICAL risk is reported to the user before
  proceeding.
- **Before modifying an API route handler**: `api_impact({route|file})`
  for consumers, accessed response fields, middleware and flows; use
  `shape_check` to catch consumer/response drift.
- **Before committing**: `detect_changes()` to confirm the diff touches only
  the expected symbols and flows; the vertical slice's quality gate
  (`shared/07` §2 G) includes it.
- **Renames** go through `rename` (call-graph aware), never find-and-replace.
- **Exploring**: `query` for concepts (process-grouped), `context` for a
  symbol's callers, callees and processes, the `context`, `clusters`,
  `processes`, `process/{name}` and `schema` resources for navigation,
  `cypher` for custom traces after reading the schema.
- **Tool servers**: `tool_map` to find MCP/RPC tool definitions and their
  handlers before changing a tool.
- When several repos are indexed, pass `repo` explicitly to every tool.

**Never**

- Edit a symbol, run impact analysis, or commit while `analyze` is in
  progress; results reflect the prior index. Safe parallel work: reading,
  planning, adding new files that touch no existing symbol, writing tests
  against unchanged surfaces, docs and config.
- Assume `.claude/` is indexed: skills, agents and their helper scripts are
  not in the graph; grep their callers.
- Treat a passing `status` as proof when a tool returns nonsense; force a
  reindex (`clean` then `analyze`).
- Assume partial freshness after a failed reindex; rerun from clean.
- Index with uncommitted changes and then stash: the index reflects the
  working tree, and the indexed SHA will not match `HEAD` until commit.

## 5. Branches and worktrees

- One index per checkout. A git worktree gets its own `.gitnexus/` and its
  own registry entry; headless agents refining different specs or features
  run in separate worktrees so their indexes and commits do not interleave.
- After switching branches, reindex before trusting any impact answer;
  the pre-edit gate exists for exactly this.
- Pipelines and chain scripts include "index on HEAD" in pre-flight
  (`shared/09` §12); a stale index fails the gate.

## 6. Groups (multi-repo products)

- A group names member repos (with optional subgroup prefixes such as
  `app/backend`, `app/frontend`) and manifest links between them. Syncing
  builds a contract registry (`contracts.json`) that extracts HTTP contracts
  and cross-links producers to consumers exactly by route and shape.
- Use `group_status` before `group_sync`; sync after changing the group
  config or re-indexing a member. `group_contracts({unmatchedOnly: true})`
  lists producers with no consumer and consumers with no producer, which is
  the cross-repo version of the API-alignment check in `shared/07` §3.
- `group_query` runs a search across every member and merges results, so a
  concept spanning backend and frontend is found once.
- The group's member list is the product's architecture boundary list; keep
  it in the repo that owns the product (the spec repo or the backend) and
  cite it from steering.

## 7. The document index

- Everything that is not code (specs, steering, ADRs, research, vault
  notes, generated docs, PDFs) is indexed by the document indexer, exposed
  as read-only MCP tools (`count`, `search`, `show`, `similar`, `stats`),
  opened `mode=ro`, rebuilt non-destructively with a shrink guard and
  history (`second-brain/01` §7).
- Search the index, not grep: count, facet, search, then show with a
  pattern. Every hit carries a citation the original can reproduce.
- Audience scoping is a hard limit on the server, not a filter per query;
  register one server per audience when sessions differ in what they may
  see.
- Where Infigraph is used it indexes the document corpus (vault, filings,
  generated docs) alongside the text index; its MCP tools follow the same
  read-only, cited, audience-scoped rules.

## 8. Enforcement

| Rule | Check |
|---|---|
| index fresh before edits | `reindex-check` skill; pipeline pre-flight asserts indexed SHA == HEAD |
| impact before symbol edit, detect_changes before commit | stated in the managed block; the review agent checks the handoff summary names the impact report |
| no notes inside the managed block | a test greps for non-generated lines between the markers |
| `.gitnexus/` ignored | `.gitignore` entry checked by the repo scaffold |
| hooks present | project `settings.json` contains the post-commit analyze hook |
| document index read-only | MCP server env opens the database `mode=ro`; a test asserts the server has no write tools |
