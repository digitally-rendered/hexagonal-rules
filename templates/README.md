# Templates

Files a project copies in when adopting the rules. Replace `<placeholders>`.

| File | Goes in | Purpose |
|---|---|---|
| `mcp-servers.json` | `~/.claude.json` (user scope) | GitNexus MCP server, once per machine |
| `mcp-project.json` | `<project>/.mcp.json` | read-only document-index servers, scoped per audience |
| `settings-hooks.json` | `<project>/.claude/settings.json` | reindex after commit, merge, checkout |
| `settings-permissions.json` | `<project>/.claude/settings.json` | pre-approve indexing commands and read-only tools |
| `claude-gitnexus-block.md` | `<project>/CLAUDE.md` | the managed block `npx gitnexus analyze` maintains; notes go outside the markers |

See `shared/12-code-intelligence-indexing.md`.
