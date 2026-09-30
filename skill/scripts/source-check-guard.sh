#!/usr/bin/env bash
# PreToolUse hook for the copy-source-checker agent. It reads untrusted pages,
# so its shell is limited to curl fetching http(s) URLs, piped only into grep,
# head or tail reading stdin. Every flag is allowlisted; anything unrecognised
# is blocked. Fails closed.
cmd=$(jq -r 'if .tool_input.command | type == "string" then .tool_input.command else empty end' 2>/dev/null)
if [ -z "$cmd" ]; then
  echo "copy-source-checker: blocked a Bash call with no command" >&2
  exit 2
fi
if python3 - "$cmd" <<'EOF'
import re, shlex, sys
cmd = sys.argv[1]

# $ expands variables and substitutions, # hides the rest of the line from
# shlex but not always from bash, and a newline starts a second command.
if any(c in cmd for c in "`$#\n\r"):
    sys.exit(1)

# Mask quoted text so shell syntax is only matched where bash would see it.
masked, quote, esc = [], None, False
for c in cmd:
    if esc:
        masked.append("x"); esc = False
    elif quote:
        masked.append("x")
        if c == quote: quote = None
        elif c == "\\" and quote == '"': esc = True
    elif c in "'\"":
        quote = c; masked.append("x")
    elif c == "\\":
        esc = True; masked.append("x")
    else:
        masked.append(c)
if quote or esc:
    sys.exit(1)
masked = "".join(masked)
if "~" in masked:
    sys.exit(1)
# An unquoted glob in a filter expands to local file names, which grep, head
# and tail would then read.
if any(ch in part for part in masked.split("|")[1:] for ch in "*?[]{}"):
    sys.exit(1)

lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
lex.whitespace_split = True
lex.commenters = ""
try:
    tokens = list(lex)
except ValueError:
    sys.exit(1)
segments, cur = [], []
for tok in tokens:
    if tok == "|":
        segments.append(cur); cur = []
    elif tok and all(c in "();<>|&" for c in tok):
        sys.exit(1)
    else:
        cur.append(tok)
segments.append(cur)

NUM = re.compile(r"\+?\d+$")

def short_flags(args, i, plain, valued):
    """Walk one -abc cluster. Returns the next index, or None to block."""
    body = args[i][1:]
    for j, c in enumerate(body):
        if c in plain:
            continue
        if c in valued:
            rest = body[j + 1:]
            if rest:
                return (i + 1, c, rest)
            if i + 1 >= len(args):
                return None
            return (i + 2, c, args[i + 1])
        return None
    return (i + 1, None, None)

def check_curl(args):
    plain_long = {"--silent", "--show-error", "--location", "--fail", "--include",
                  "--head", "--get", "--compressed"}
    valued_long = {"--user-agent": "A", "--header": "H", "--max-time": "m", "--retry": "r"}
    urls, i = 0, 0
    while i < len(args):
        a = args[i]
        if a.startswith("--"):
            name, eq, val = a.partition("=")
            if name in plain_long and not eq:
                i += 1; continue
            if name not in valued_long:
                return False
            if not eq:
                if i + 1 >= len(args):
                    return False
                val = args[i + 1]; i += 1
            flag = valued_long[name]; i += 1
        elif a.startswith("-") and len(a) > 1:
            step = short_flags(args, i, "sSLfiIG", "AHm")
            if step is None:
                return False
            i, flag, val = step
            if flag is None:
                continue
        else:
            if not re.match(r"https?://", a, re.I):
                return False
            urls += 1; i += 1; continue
        if val.startswith("@"):
            return False
        if flag in "mr" and not re.match(r"\d+(\.\d+)?$", val):
            return False
    return urls > 0

def check_grep(args):
    patterns, positional, i = 0, 0, 0
    while i < len(args):
        a = args[i]
        if a.startswith("-") and len(a) > 1 and not a.startswith("--"):
            step = short_flags(args, i, "iEFocnwvx", "mABCe")
            if step is None:
                return False
            i, flag, val = step
            if flag == "e":
                patterns += 1
            elif flag is not None and not NUM.match(val):
                return False
        elif a.startswith("-"):
            return False
        else:
            positional += 1; i += 1
    return positional == (0 if patterns else 1)

def check_head_tail(args):
    i = 0
    while i < len(args):
        a = args[i]
        if re.match(r"-\d+$", a):
            i += 1; continue
        m = re.match(r"-([nc])(.*)$", a)
        if not m:
            return False
        val = m.group(2)
        if not val:
            if i + 1 >= len(args):
                return False
            val = args[i + 1]; i += 1
        if not NUM.match(val):
            return False
        i += 1
    return True

first = segments[0]
if not first or first[0] != "curl" or not check_curl(first[1:]):
    sys.exit(1)
filters = {"grep": check_grep, "head": check_head_tail, "tail": check_head_tail}
for words in segments[1:]:
    if not words or words[0] not in filters or not filters[words[0]](words[1:]):
        sys.exit(1)
sys.exit(0)
EOF
then
  exit 0
fi
echo "copy-source-checker may run curl on quoted http(s) URLs with fetch flags only (-s -S -L -f -i -I -G -A -H -m --compressed), piped only into grep, head or tail reading stdin; blocked: $cmd" >&2
exit 2
