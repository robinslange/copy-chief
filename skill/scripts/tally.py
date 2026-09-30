#!/usr/bin/env python3
"""Majority vote over copy-grader runs.

Each run ends with FIRED:, NA: and GATE0: lines. A check is a finding when a
strict majority of runs fired it, and not applicable when a strict majority
marked it so. A check fired by a minority is reported as unstable. Gate 0 is
blocked if any run blocked it, because its failure is silent.
"""
import re
import sys

CHECKS = ["M1", "M2", "M3", "M4", "O1", "O2", "O3", "O4", "H1", "H2", "H3", "H4",
          "P1", "P2", "P3", "P4", "V1", "V2", "V3", "V4", "C1", "C2", "C3", "X1", "X2"]


def _ids(field):
    field = field.strip()
    if field.lower() == "none" or field == "":
        return set()
    ids = {i.strip().upper() for i in field.split(",") if i.strip()}
    unknown = ids - set(CHECKS)
    if unknown:
        raise ValueError(f"unknown check id: {', '.join(sorted(unknown))}")
    return ids


def parse(text):
    found = {}
    for key in ("FIRED", "NA", "GATE0"):
        lines = re.findall(rf"^{key}:(.*)$", text, flags=re.M)
        if not lines:
            raise ValueError(f"missing {key}: line")
        found[key] = lines[-1]
    gate = found["GATE0"].strip().upper()
    if gate not in ("BLOCKED", "CLEAR"):
        raise ValueError(f"GATE0 must be BLOCKED or CLEAR, got {gate!r}")
    return {"fired": _ids(found["FIRED"]), "na": _ids(found["NA"]), "blocked": gate == "BLOCKED"}


def tally(runs):
    parsed = [parse(r) for r in runs]
    n = len(parsed)
    fired = {c: sum(c in p["fired"] for p in parsed) for c in CHECKS}
    na = {c: sum(c in p["na"] for p in parsed) for c in CHECKS}
    na_major = [c for c in CHECKS if na[c] * 2 > n]
    findings = [c for c in CHECKS if fired[c] * 2 > n and c not in na_major]
    unstable = [(c, fired[c]) for c in CHECKS if 0 < fired[c] and fired[c] * 2 <= n and c not in na_major]
    return {"findings": findings, "unstable": unstable, "na": na_major,
            "gate_blocked_runs": sum(p["blocked"] for p in parsed), "runs": n}


def main(paths):
    if not paths:
        print("usage: tally.py run1.md [run2.md ...]", file=sys.stderr)
        return 1
    texts = []
    for p in paths:
        try:
            text = open(p).read()
            parse(text)
        except (OSError, ValueError) as e:
            print(f"{p}: {e}", file=sys.stderr)
            return 1
        texts.append(text)
    r = tally(texts)
    n = r["runs"]
    print("FINDINGS: " + (",".join(r["findings"]) or "none"))
    print("UNSTABLE: " + (", ".join(f"{c} ({k}/{n})" for c, k in r["unstable"]) or "none"))
    print("NOT-APPLICABLE: " + (",".join(r["na"]) or "none"))
    g = r["gate_blocked_runs"]
    print(f"GATE0: {'BLOCKED' if g else 'CLEAR'} ({g}/{n} runs)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
