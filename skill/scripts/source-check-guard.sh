#!/usr/bin/env bash
# PreToolUse hook for the copy-source-checker agent. It reads untrusted pages,
# so its shell is limited to curl, piped only into grep, head or tail. No
# chaining, redirection, substitution, file writes or uploads. Fails closed.
cmd=$(jq -r 'if .tool_input.command | type == "string" then .tool_input.command else empty end' 2>/dev/null)
if [ -z "$cmd" ]; then
  echo "copy-source-checker: blocked a Bash call with no command" >&2
  exit 2
fi
if python3 - "$cmd" <<'EOF'
import shlex, sys
cmd = sys.argv[1]
if any(t in cmd for t in ("`", "$(", "\n")):
    sys.exit(1)
lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lex.whitespace_split = True
tokens = list(lex)
segments, cur = [], []
for tok in tokens:
    if tok == "|":
        segments.append(cur); cur = []
    elif tok and all(c in "();<>|&" for c in tok):
        sys.exit(1)
    else:
        cur.append(tok)
segments.append(cur)
first = segments[0]
if not first or first[0] != "curl":
    sys.exit(1)
banned = ("-o", "--output", "-O", "--remote-name", "-T", "--upload-file",
          "-d", "--data", "-F", "--form", "-K", "--config", "--json")
for arg in first[1:]:
    if arg.startswith("@") or any(arg == b or arg.startswith(b + "=") or
                                  (b.startswith("--") and arg.startswith(b)) for b in banned):
        sys.exit(1)
    if len(arg) > 2 and arg[0] == "-" and arg[1] != "-" and any(f in arg[1:] for f in "oOTdFK"):
        sys.exit(1)
for words in segments[1:]:
    if not words or words[0] not in ("grep", "head", "tail"):
        sys.exit(1)
sys.exit(0)
EOF
then
  exit 0
fi
echo "copy-source-checker may run curl, piped only into grep, head or tail; blocked: $cmd" >&2
exit 2
