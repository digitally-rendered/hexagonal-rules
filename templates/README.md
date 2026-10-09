# Templates

Files a project copies in when adopting the rules. Replace `<placeholders>`.

| File | Goes in | Purpose |
|---|---|---|
| `mcp-servers.json` | `~/.claude.json` (user scope) | GitNexus MCP server, once per machine |
| `mcp-project.json` | `<project>/.mcp.json` | read-only document-index servers, scoped per audience |
| `settings-hooks.json` | `~/.claude/settings.json` (user scope) | reindex after git commands that move HEAD, via the hook script |
| `gitnexus-reindex-hook.sh` | `~/.claude/hooks/` (user scope, outside any repo) | the hook body: parses the tool call JSON on stdin in isolated Python, never evaluates command text |
| `settings-permissions.json` | `<project>/.claude/settings.json` | pre-approve indexing commands and read-only tools |
| `claude-gitnexus-block.md` | `<project>/CLAUDE.md` | the managed block `npx gitnexus analyze` maintains; notes go outside the markers |

See `shared/12-code-intelligence-indexing.md`.
