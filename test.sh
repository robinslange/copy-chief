#!/usr/bin/env bash
# Runs every test suite. Exits non-zero if any suite fails.
set -u
here=$(cd "$(dirname "$0")" && pwd)
export PYTHONDONTWRITEBYTECODE=1
status=0
run() { # run <label> <command...>
  local label=$1; shift
  if out=$("$@" 2>&1); then
    echo "pass  $label"
  else
    echo "FAIL  $label"; echo "$out" | grep -E "FAIL|Error|error" | sed 's/^/      /'; status=1
  fi
}
run "grader read guard"   bash "$here/skill/tests/grader-read-guard.test.sh"
run "source check guard"  bash "$here/skill/tests/source-check-guard.test.sh"
run "tally"               python3 -m unittest -q "$here/skill/tests/test_tally.py"
run "install"             bash "$here/tests/install.test.sh"
run "contracts"           python3 -m unittest -q "$here/tests/test_contract.py"
run "no private content"  python3 -m unittest -q "$here/tests/test_private.py"
run "shell syntax"        bash -c 'for f in "$0"/install.sh "$0"/test.sh "$0"/skill/scripts/*.sh "$0"/skill/tests/*.sh "$0"/tests/*.sh; do bash -n "$f" || exit 1; done' "$here"
exit $status
