#!/usr/bin/env bash
# Links copy-chief into ~/.claude: the skill and its two agents point back at
# this checkout, so a git pull here updates the installed copy.
set -euo pipefail
here=$(cd "$(dirname "$0")" && pwd)
for dep in jq python3; do
  command -v "$dep" >/dev/null || { echo "copy-chief needs $dep on PATH" >&2; exit 1; }
done
mkdir -p "$HOME/.claude/skills" "$HOME/.claude/agents"
link() { # link <target> <link path>
  if [ -e "$2" ] && [ ! -L "$2" ]; then
    echo "$2 exists and is not a symlink; move it aside first" >&2; exit 1
  fi
  ln -sfn "$1" "$2"
}
link "$here/skill" "$HOME/.claude/skills/copy-chief"
for a in copy-grader copy-source-checker; do
  link "$here/agents/$a.md" "$HOME/.claude/agents/$a.md"
done
chmod +x "$here/skill/scripts/"*.sh
echo "linked. restart claude code, then run /copy-chief <draft>"
