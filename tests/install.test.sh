#!/usr/bin/env bash
# Tests for install.sh. Every case runs against a throwaway HOME.
set -u
repo="$(cd "$(dirname "$0")/.." && pwd)"
tmp=$(mktemp -d); trap 'rm -rf "$tmp"' EXIT
fail=0
ok() { echo "ok   $1"; }
bad() { echo "FAIL $1"; fail=1; }
check() { if eval "$2"; then ok "$1"; else bad "$1"; fi; }

h="$tmp/home one"; mkdir -p "$h"
HOME="$h" bash "$repo/install.sh" >/dev/null 2>&1
check "install exits 0" '[ $? -eq 0 ]'
check "skill is a symlink to the checkout" '[ "$(readlink "$h/.claude/skills/copy-chief")" = "$repo/skill" ]'
for a in copy-grader copy-source-checker; do
  check "$a is a symlink to the checkout" '[ "$(readlink "$h/.claude/agents/$a.md")" = "$repo/agents/$a.md" ]'
done
check "guards are executable" '[ -x "$repo/skill/scripts/grader-read-guard.sh" ] && [ -x "$repo/skill/scripts/source-check-guard.sh" ]'

HOME="$h" bash "$repo/install.sh" >/dev/null 2>&1
check "rerun is idempotent" '[ $? -eq 0 ] && [ "$(readlink "$h/.claude/skills/copy-chief")" = "$repo/skill" ]'
check "rerun does not nest a link inside the skill" '[ ! -e "$repo/skill/skill" ]'

h2="$tmp/stale"; mkdir -p "$h2/.claude/skills" "$h2/.claude/agents"
ln -s /nonexistent "$h2/.claude/skills/copy-chief"
ln -s /nonexistent "$h2/.claude/agents/copy-grader.md"
HOME="$h2" bash "$repo/install.sh" >/dev/null 2>&1
check "stale symlinks are replaced" '[ "$(readlink "$h2/.claude/skills/copy-chief")" = "$repo/skill" ] && [ "$(readlink "$h2/.claude/agents/copy-grader.md")" = "$repo/agents/copy-grader.md" ]'

h3="$tmp/real"; mkdir -p "$h3/.claude/skills/copy-chief"; echo mine > "$h3/.claude/skills/copy-chief/SKILL.md"
HOME="$h3" bash "$repo/install.sh" >/dev/null 2>&1
check "a real skill directory stops the install" '[ $? -ne 0 ]'
check "a real skill directory is left untouched" '[ ! -L "$h3/.claude/skills/copy-chief" ] && [ "$(cat "$h3/.claude/skills/copy-chief/SKILL.md")" = mine ]'

h4="$tmp/realagent"; mkdir -p "$h4/.claude/agents"; echo mine > "$h4/.claude/agents/copy-source-checker.md"
HOME="$h4" bash "$repo/install.sh" >/dev/null 2>&1
check "a real agent file stops the install" '[ $? -ne 0 ] && [ "$(cat "$h4/.claude/agents/copy-source-checker.md")" = mine ]'

# Missing dependencies stop the install before anything is linked.
for dep in jq python3; do
  bin="$tmp/bin-$dep"; mkdir -p "$bin"
  for t in bash dirname mkdir ln chmod rm jq python3; do
    [ "$t" = "$dep" ] || ln -sf "$(command -v "$t")" "$bin/$t"
  done
  hd="$tmp/no-$dep"; mkdir -p "$hd"
  HOME="$hd" PATH="$bin" "$bin/bash" "$repo/install.sh" >/dev/null 2>&1
  check "missing $dep stops the install" '[ $? -ne 0 ] && [ ! -e "$hd/.claude/skills/copy-chief" ]'
done

# End to end: through the installed links, the agent's hook command resolves
# to the guard, and the guard admits the rubric and blocks the answer key.
hook=$(grep -m1 'command:' "$h/.claude/agents/copy-grader.md" | sed 's/.*command: *"\(.*\)"/\1/')
hook=${hook//\$HOME/$h}
check "grader hook command resolves to an executable" '[ -x "$hook" ]'
read_as() { printf '{"tool_input":{"file_path":"%s"}}' "$1" | HOME="$h" bash "$hook" >/dev/null 2>&1; echo $?; }
check "installed guard admits the rubric by ~ path" '[ "$(read_as "~/.claude/skills/copy-chief/references/checks.md")" = 0 ]'
check "installed guard blocks the answer key" '[ "$(read_as "~/.claude/skills/copy-chief/fixtures/planted-key.md")" = 2 ]'
shook=$(grep -m1 'command:' "$h/.claude/agents/copy-source-checker.md" | sed 's/.*command: *"\(.*\)"/\1/')
shook=${shook//\$HOME/$h}
check "source-checker hook command resolves to an executable" '[ -x "$shook" ]'
exit $fail
