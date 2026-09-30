#!/usr/bin/env bash
# Installs copy-chief into ~/.claude: the skill, its two agents, and their hook paths.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
for dep in jq python3; do
  command -v "$dep" >/dev/null || { echo "copy-chief needs $dep on PATH" >&2; exit 1; }
done
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
rm -rf "$HOME/.claude/skills/copy-chief"
cp -R "$here/skill" "$HOME/.claude/skills/copy-chief"
chmod +x "$HOME/.claude/skills/copy-chief/scripts/"*.sh
for a in copy-grader copy-source-checker; do
  sed "s|__HOME__|$HOME|g" "$here/agents/$a.md" > "$HOME/.claude/agents/$a.md"
done
echo "installed. restart claude code, then run /copy-chief <draft>"
