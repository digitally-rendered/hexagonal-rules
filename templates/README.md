# Templates

Files a project copies in when adopting the rules. Replace `<placeholders>`.

| File | Goes in | Purpose |
|---|---|---|
| `mcp-servers.json` | `~/.claude.json` (user scope) | GitNexus MCP server ([project repository](https://github.com/abhigyanpatwari/GitNexus)), once per machine; pin the installed version in the project's tooling manifest |
| `mcp-project.json` | `<project>/.mcp.json` | read-only document-index servers (`<document-index-module>` placeholder), one per audience |
| `settings-hooks.json` | `~/.claude/settings.json` (user scope) | reindex after git commands that move HEAD, via the hook script |
| `gitnexus-reindex-hook.sh` | `~/.claude/hooks/` (user scope, outside any repo) | the hook body: captures the tool-call JSON from stdin, parses it in isolated Python, never evaluates command text |
| `test-reindex-hook.sh` | run in place: `sh templates/test-reindex-hook.sh` | test for the hook: a stub `gitnexus` on PATH must be called for a HEAD-moving git command and not for anything else; run it after any change to the hook |
| `settings-permissions.json` | `<project>/.claude/settings.json` | pre-approve the installed `gitnexus` binary with exact subcommands and the read-only tools |
| `settings-permissions-design.json` | `<project>/.claude/settings.json` | pre-approve only the read tools of a design-tool MCP server (`design-tool`); write tools stay prompted, which is what makes the server read-only in practice |
| `claude-gitnexus-block.md` | `<project>/CLAUDE.md` | the managed block `gitnexus analyze` maintains; notes go outside the markers |

See `shared/12-code-intelligence-indexing.md` and, for the design server,
`typescript/13-design-system-and-figma.md`.
