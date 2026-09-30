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
expect 0 "$(json "$cc/references//checks.md")"                   "doubled slash normalises to checks.md"
expect 2 "$(json "$cc/references")"                             "the references directory blocked"
expect 2 "$(json "$tmp/checks.md")"                              "a checks.md elsewhere blocked"
expect 2 "$(json "")"                                            "empty file_path blocked"
expect 2 '{"tool_name":"Read","tool_input":{"file_path":["x"]}}' "non-string file_path blocked"
expect 2 '{"tool_name":"Read","tool_input":{}}'                  "missing file_path blocked"
expect 2 'not json'                                              "garbage input blocked"

# The install layout: the skill directory is a symlink into a repo checkout.
linked="$tmp/linked home"; mkdir -p "$linked/.claude/skills"
ln -s "$cc" "$linked/.claude/skills/copy-chief"
through() { # through <code> <path> <label>
  printf '%s' "$(json "$2")" | HOME="$linked" bash "$guard" >/dev/null 2>&1
  got=$?
  if [ "$got" -ne "$1" ]; then echo "FAIL $3: want $1 got $got"; fail=1; else echo "ok   $3"; fi
}
through 0 "~/.claude/skills/copy-chief/references/checks.md"   "checks.md through a symlinked install allowed"
through 0 "$cc/references/ai-tells.md"                         "real path of a linked rubric allowed"
through 2 "~/.claude/skills/copy-chief/fixtures/planted-key.md" "key through a symlinked install blocked"

# A missing dependency must fail closed: probe with the one path that would
# otherwise be allowed, so a pass proves the guard blocked, not the path.
bin="$tmp/bin"; mkdir -p "$bin"
missing() { # missing <tool to leave out> <label>
  rm -f "$bin"/*
  for t in jq python3; do [ "$t" = "$1" ] || ln -s "$(command -v "$t")" "$bin/$t"; done
  printf '%s' "$(json "$cc/references/checks.md")" | HOME="$tmp" PATH="$bin" /bin/bash "$guard" >/dev/null 2>&1
  got=$?
  if [ "$got" -ne 2 ]; then echo "FAIL $2: want 2 got $got"; fail=1; else echo "ok   $2"; fi
}
missing python3 "python3 missing blocks"
missing jq      "jq missing blocks"
exit $fail
