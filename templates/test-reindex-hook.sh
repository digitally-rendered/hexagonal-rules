#!/bin/sh
# Test for gitnexus-reindex-hook.sh: the hook must call `gitnexus analyze`
# after a git command that moves HEAD, and must not call it otherwise.
#
# Run from anywhere:  sh templates/test-reindex-hook.sh
# Exit code 0 = pass, 1 = a case failed. Nothing outside a temp dir is touched;
# a stub `gitnexus` on PATH records its invocation instead of indexing.
set -eu
here="$(cd "$(dirname "$0")" && pwd)"
hook="$here/gitnexus-reindex-hook.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

marker="$tmp/called"
mkdir "$tmp/bin"
cat >"$tmp/bin/gitnexus" <<EOF
#!/bin/sh
printf '%s\n' "\$*" >>"$marker"
EOF
chmod +x "$tmp/bin/gitnexus"
export PATH="$tmp/bin:$PATH"

fail=0
run_case() {  # name, expect (called|not-called), payload
  name="$1"; expect="$2"; payload="$3"
  rm -f "$marker"
  printf '%s' "$payload" | sh "$hook"
  if [ -f "$marker" ]; then got="called"; else got="not-called"; fi
  if [ "$got" = "$expect" ]; then
    echo "PASS  $name ($got)"
  else
    echo "FAIL  $name: expected $expect, got $got"; fail=1
  fi
}

run_case "git commit reindexes" called \
  '{"tool_name":"Bash","tool_input":{"command":"git commit -m \"x\""}}'
run_case "git checkout reindexes" called \
  '{"tool_name":"Bash","tool_input":{"command":"cd repo && git checkout main"}}'
run_case "non-git Bash command does not reindex" not-called \
  '{"tool_name":"Bash","tool_input":{"command":"ls -la"}}'
run_case "git status does not reindex" not-called \
  '{"tool_name":"Bash","tool_input":{"command":"git status"}}'
run_case "non-Bash tool does not reindex" not-called \
  '{"tool_name":"Read","tool_input":{"file_path":"git commit"}}'
run_case "empty stdin does not reindex" not-called ''
run_case "malformed JSON does not reindex" not-called 'git commit'

if [ "$fail" -eq 0 ]; then
  # the positive case must have passed the subcommand through
  printf '%s' '{"tool_name":"Bash","tool_input":{"command":"git merge x"}}' | sh "$hook"
  if grep -qx 'analyze' "$marker"; then echo "PASS  stub received 'analyze'"; else echo "FAIL  stub args: $(cat "$marker")"; fail=1; fi
fi
[ "$fail" -eq 0 ] && echo "all hook cases passed"
exit "$fail"
