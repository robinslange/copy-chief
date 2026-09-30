#!/usr/bin/env bash
# Tests for grader-read-guard.sh. Runs against a throwaway HOME.
set -u
guard="$(cd "$(dirname "$0")/.." && pwd)/scripts/grader-read-guard.sh"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
cc="$tmp/.claude/skills/copy-chief"
mkdir -p "$cc/references" "$cc/fixtures"
echo rubric > "$cc/references/checks.md"
echo tells > "$cc/references/ai-tells.md"
echo key > "$cc/fixtures/planted-key.md"
ln -s "$cc/fixtures/planted-key.md" "$cc/references/sneaky.md"

fail=0
expect() { # expect <code> <json> <label>
  printf '%s' "$2" | HOME="$tmp" bash "$guard" >/dev/null 2>&1
  got=$?
  if [ "$got" -ne "$1" ]; then echo "FAIL $3: want $1 got $got"; fail=1; else echo "ok   $3"; fi
}
json() { printf '{"tool_name":"Read","tool_input":{"file_path":"%s"}}' "$1"; }

expect 0 "$(json "$cc/references/checks.md")"                    "checks.md allowed"
expect 0 "$(json "$cc/references/ai-tells.md")"                  "ai-tells.md allowed"
expect 2 "$(json "$cc/fixtures/planted-key.md")"                 "fixtures blocked"
expect 2 "$(json "$cc/references/../fixtures/planted-key.md")"   "dot-dot traversal blocked"
expect 2 "$(json "$cc/references/sneaky.md")"                    "symlink into fixtures blocked"
expect 2 "$(json "$cc/references/canon.md")"                     "canon.md blocked"
expect 2 "$(json "$tmp/.claude/CLAUDE.md")"                      "CLAUDE.md blocked"
expect 0 "$(json "~/.claude/skills/copy-chief/references/checks.md")" "~ path to checks.md allowed"
expect 2 "$(json "~/.claude/skills/copy-chief/fixtures/planted-key.md")" "~ path to fixtures blocked"
expect 2 '{"tool_name":"Read","tool_input":{}}'                  "missing file_path blocked"
expect 2 'not json'                                              "garbage input blocked"

# python3 missing: realpath cannot resolve, so the guard must fail closed.
nopy="$tmp/nopy"; mkdir -p "$nopy"; ln -s "$(command -v jq)" "$nopy/jq"
printf '%s' "$(json "$tmp/.claude/CLAUDE.md")" | HOME="$tmp" PATH="$nopy" /bin/bash "$guard" >/dev/null 2>&1
got=$?
if [ "$got" -ne 2 ]; then echo "FAIL python3 missing blocks: want 2 got $got"; fail=1; else echo "ok   python3 missing blocks"; fi
exit $fail
