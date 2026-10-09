#!/bin/sh
# PostToolUse hook: reindex with GitNexus after a git command that moves HEAD.
#
# Install at USER scope (~/.claude/hooks/), not in a repository: a hook path
# inside a repo is code that anyone who commits to that repo can change, and it
# would run automatically in every contributor's session.
#
# Claude Code passes the tool call as JSON on stdin. The command string is only
# inspected by a JSON parser, never evaluated. Python runs in isolated mode
# (-I) so a module planted in the repository (json.py, re.py) cannot be
# imported in place of the standard library.
set -eu
should_reindex="$(python3 -I - <<'PY'
import json, re, sys
try:
    payload = json.load(sys.stdin)
except Exception:
    print("no"); sys.exit(0)
if payload.get("tool_name") != "Bash":
    print("no"); sys.exit(0)
cmd = str(payload.get("tool_input", {}).get("command", ""))
print("yes" if re.search(r"\bgit\s+(commit|merge|checkout|switch|pull|rebase)\b", cmd) else "no")
PY
)"
if [ "$should_reindex" = "yes" ] && command -v gitnexus >/dev/null 2>&1; then
  gitnexus analyze >/dev/null 2>&1 || true
fi
exit 0
