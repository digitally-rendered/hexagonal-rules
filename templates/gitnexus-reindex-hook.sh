#!/bin/sh
# PostToolUse hook: reindex with GitNexus after a git command that moves HEAD.
# Claude Code passes the tool call as JSON on stdin; the command string is never
# evaluated, only inspected by a JSON parser, so tool input cannot inject here.
set -eu
should_reindex="$(python3 - <<'PY'
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
if [ "$should_reindex" = "yes" ]; then
  command -v gitnexus >/dev/null 2>&1 && gitnexus analyze >/dev/null 2>&1 || true
fi
exit 0
