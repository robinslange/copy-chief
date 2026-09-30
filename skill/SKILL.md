---
name: copy-chief
description: Use when the user asks to review, grade, critique or tighten a piece of copy (an ad, landing page, email, carousel, subject line or caption) or asks for a copy brief before writing one. Runs a binary source gate plus 25 direct-response checks, each traced to the principle it enforces, and returns line-level findings with a BLOCKED or PASS-WITH-FINDINGS verdict. Never rewrites the draft unless asked, never produces a score. Brand-agnostic; composes with any brand-specific skill rather than replacing its non-negotiables.
---

# Copy Chief

A cold gate for direct response copy. Grades drafts; it does not write them.

## The cold run, non-negotiable

Grading happens in the `copy-grader` agent, never in this conversation. The
harness keeps it cold: it launches without CLAUDE.md, its only tool is Read,
and a hook blocks every read except `checks.md` and `ai-tells.md`. Its prompt
contains exactly:

1. The draft, verbatim, between `<<<` and `>>>`.
2. The medium, the jurisdiction, and whether the piece is the closing unit,
   if known (one line each). See "Closing unit" in `checks.md`.

Never the brief, the conversation that produced the draft, the author's
reasoning, a file path, or any earlier grade.

The separation matters because the author's knowledge is an instrument with
its own blind spot. On code, an author's self-review and a cold review found
disjoint defects (`the-cold-review-and-the-self-review-found-disjoint-defects`),
and a cold reviewer found fourteen issues a self-review had passed
(`an-independent-adversarial-subagent-review-catches-build-breakers-a-self-review-misses`).
That evidence comes from code review. It has not been measured on copy. If you
grade in-conversation because it seemed faster, the grade is void.

Dispatch `copy-grader` as a plain subagent: `subagent_type` only, never a
`name`. A named spawn runs as a teammate, and teammates skip the agent's
frontmatter hooks: on 2026-09-28 a named copy-grader read the fixture answer
key while a plain one, same prompt, was blocked.

The hook is the guarantee, and only a live test proves it is wired: dispatch
`copy-grader` the same way you grade with it, with an instruction to read
`fixtures/planted-key.md`, and check that the tool returns the guard's
"blocked" message. A missing or
non-executable script lets reads through, because the harness treats any exit
code but 2 as non-blocking.

The hook lives in `copy-grader`'s frontmatter, and the harness applies it only
to a plain subagent dispatch. Dispatch every grader, including the live test,
with `subagent_type: copy-grader` and no `name` or team. A grader spawned as a
named teammate reads `fixtures/planted-key.md` unblocked; this was checked live
on 2026-09-28. Paste the draft text itself into the prompt: tool prompts are
not run through a shell, so `$(cat draft.md)` arrives as literal text.

### Three runs, majority per check

A single grader's verdict drifts between runs, and drifts more on long input.
Dispatch `copy-grader` three times in parallel, in one message, with the
identical prompt. Save each report verbatim to `run1.md`, `run2.md` and
`run3.md` in a fresh directory under the session's scratchpad (or
`$TMPDIR/copy-chief/<timestamp>/` when there is none), then run:

    python3 ~/.claude/skills/copy-chief/scripts/tally.py run1.md run2.md run3.md

A check is a finding when at least two runs fired it. A check fired by one run
is listed as unstable and is not a finding. Gate 0 is blocked if any run
blocked it. If tally.py exits 1, a run broke: re-dispatch that run, never
count it as clean.

For each finding, report the wording from the lowest-numbered run that fired
it. For Gate 0, list the union of every run's items.

### Sources

If the draft cites anything (a PMID, a DOI, a URL, a named study, a
regulation), dispatch `copy-source-checker` once with the draft between
`<<<` and `>>>`. Any `DOES NOT SUPPORT` or `UNRESOLVABLE` verdict joins the
Gate 0 block with the source's own sentence quoted. A cited source that
resolves and supports its sentence clears that item.
Report every NOTES line the checker returns under Sources, quoted, even when
its verdict is SUPPORTS: a paper that supports one sentence can contradict the
next.

## Modes

### `/copy-chief <draft|path>`, diagnostic (default)

1. Dispatch three `copy-grader` runs and tally them.
2. If the draft cites sources, dispatch `copy-source-checker`.
3. Report.

### `/copy-chief --brief`, pre-writing

Read `references/canon.md` first. Each declaration below is answered against
its canon section, and a declaration that cannot say which state or stage the
section names is not made yet.

Refuse to draft until five declarations exist:

1. Awareness stage of the reader. Canon §1.
2. Market sophistication stage. Canon §2.
3. The one reader, named specifically enough to picture. Canon §9.
4. The offer in one sentence. Canon §4.
5. The proof inventory: every claim that will need a source, listed before
   writing, so Gate 0 has nothing to catch later. Canon §6.

This mode is where the copy gets better. The diagnostic mode only stops drafts
being wrong.

## Output contract

- **Verdict line:** `BLOCKED` (Gate 0 failed) or `PASS-WITH-FINDINGS`.
- **Closing unit line:** whether the piece is the closing unit, and if not,
  the Offer and Close checks reported as not applicable.
- **Gate 0 block**, if any: each unsourced item, quoted, with what would source it.
- **Findings**, severity-ranked, each as: check id, quoted line, what fails,
  the principle it violates. Name the principle every time; that's how the
  canon gets learned, by being hit with it.
- **Unstable:** one line listing checks that fired in only one of three runs,
  as `H4 (1/3)`. Not findings; shown so a pattern across drafts is visible.
- **Sources:** one line per checked citation with its verdict, followed by
  the checker's NOTES for that citation, when the source checker ran.
- **No score.** No 0-100, no letter, no "7/10". A composite hides which check
  failed, and which check failed is the only information this instrument
  produces.
- Do not rewrite the draft. If the user asks for a rewrite, that is a second,
  explicit pass they ask for.

Gate 0 and the 25 checks are counted separately. A draft can be BLOCKED by
Gate 0 while passing all 25 checks: that is a coherent, expected result, not
a contradiction. Gate 0 asks "is every claim sourced," the checks ask "is the
copy any good." A draft can fail the first question and pass the second.
Don't read a BLOCKED verdict next to a clean check list as a graded error.

## Scope

Grades the copy in front of it. Does not replace a brand skill's
non-negotiables (product verification, claim posture, voice lock, disclaimer
placement); those live in whatever brand skill you pair it with and still
apply on top of this gate.

`references/canon.md` is never given to the cold grader. After a report, when
the user wants the depth behind a finding, find the section whose "Enforced by"
line names that check id and open the vault notes it routes to.
