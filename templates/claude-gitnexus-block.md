<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **<repo-name>**. Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `gitnexus analyze` (the installed binary, pre-approved in `settings-permissions.json`) in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user. <!-- lint: ok -->
- **MUST run `gitnexus_api_impact` before modifying an API route handler.** <!-- lint: ok -->
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. <!-- lint: ok -->
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits. <!-- lint: ok -->
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping.
- For full context on a symbol — callers, callees, execution flows — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it. <!-- lint: ok -->
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis. <!-- lint: ok -->
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph. <!-- lint: ok -->
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope. <!-- lint: ok -->

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/<repo-name>/context` | Codebase overview, check index freshness |
| `gitnexus://repo/<repo-name>/clusters` | All functional areas |
| `gitnexus://repo/<repo-name>/processes` | All execution flows |
| `gitnexus://repo/<repo-name>/process/{name}` | Step-by-step execution trace |
| `gitnexus://repo/<repo-name>/schema` | Graph schema for Cypher |

## Skills

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |
| Is the index fresh? | `.claude/skills/reindex-check/SKILL.md` |

<!-- gitnexus:end -->
