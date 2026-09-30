#!/usr/bin/env bash
# PreToolUse hook for the copy-grader agent. The grader may read the two rubric
# files and nothing else, so it never sees a fixture's answer key, the brief, or
# canon.md. Paths are resolved first, so ../ and symlinks cannot route around it.
refs="$HOME/.claude/skills/copy-chief/references"
path=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
if [ -z "$path" ]; then
  echo "copy-grader: blocked a Read with no file_path" >&2
  exit 2
fi
real() { python3 -c 'import os,sys; print(os.path.realpath(os.path.expanduser(sys.argv[1])))' "$1"; }
target=$(real "$path") && checks=$(real "$refs/checks.md") && tells=$(real "$refs/ai-tells.md")
if [ -z "$target" ] || [ -z "$checks" ] || [ -z "$tells" ]; then
  echo "copy-grader: could not resolve paths (python3 unavailable?); blocking" >&2
  exit 2
fi
if [ "$target" = "$checks" ] || [ "$target" = "$tells" ]; then
  exit 0
fi
echo "copy-grader may read only references/checks.md and references/ai-tells.md; blocked: $path" >&2
exit 2
