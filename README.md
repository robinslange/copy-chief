# copy-chief

A cold gate for direct-response copy, built as a [Claude Code](https://claude.com/claude-code) skill. It grades drafts instead of writing them.

Give it an ad, landing page, email, carousel, subject line or caption. It returns line-level findings against a binary source gate (Gate 0) and 25 direct-response checks. Each finding is traced to the principle it enforces, drawn from Schwartz, Hopkins, Halbert, Sugarman, Cialdini, Kennedy and others. The verdict is `BLOCKED` or `PASS-WITH-FINDINGS`. You never get a score, because a composite number hides which check failed, and that is the only thing worth knowing.

## How it works

- **Cold grading.** A separate `copy-grader` agent does the grading. It never sees your brief, your conversation or your reasoning. It gets only the draft. A hook limits its reads to the two rubric files, so it can't peek at answer keys or earlier grades.
- **Three runs, majority vote.** Grader verdicts drift between runs. copy-chief runs three graders in parallel, and `scripts/tally.py` keeps a check only when at least two of them fired it. A check that fires in one run is shown as unstable, not as a finding.
- **Sources get read.** If the draft cites a PMID, DOI, URL, study or regulation, a `copy-source-checker` agent fetches the source and quotes the sentence that supports or contradicts the claim. A hook restricts its shell to read-only `curl`.
- **Brief mode.** `/copy-chief --brief` refuses to draft until you've declared the awareness stage, market sophistication, the one reader, the offer and the proof inventory.

## Install

Needs Claude Code, `jq` and `python3`.

```sh
git clone https://github.com/robinslange/copy-chief.git
cd copy-chief
./install.sh
```

This copies the skill to `~/.claude/skills/copy-chief` and the two agents to `~/.claude/agents/`. Restart Claude Code, then:

```
/copy-chief path/to/draft.md
```

or paste a draft and ask Claude to run copy-chief on it.

### Check the guard is live

The cold run is only as cold as its hook. After installing, ask Claude to dispatch `copy-grader` with the instruction "read `~/.claude/skills/copy-chief/fixtures/planted-key.md`". The read should come back blocked. Dispatch it as a plain subagent: named or teammate spawns skip agent-frontmatter hooks.

## What's in here

| path | what |
|---|---|
| `skill/SKILL.md` | the orchestrator: modes, dispatch rules, output contract |
| `skill/references/checks.md` | Gate 0 and the 25 checks the grader applies |
| `skill/references/ai-tells.md` | AI-prose tells the grader flags |
| `skill/references/canon.md` | the ten mechanisms behind the checks, for brief mode and follow-up (never given to the grader) |
| `skill/scripts/` | read guards for both agents, and the three-run tally |
| `skill/tests/` | tests for the guards and the tally |
| `skill/fixtures/` | a planted-defect draft with its key, a clean draft, and minimal pairs for the six loudest checks with their measured runs |
| `agents/` | the `copy-grader` and `copy-source-checker` agent definitions |

Run the tests with:

```sh
cd skill
bash tests/grader-read-guard.test.sh
bash tests/source-check-guard.test.sh
python3 -m pytest tests/test_tally.py
```

## Notes

- The backticked `vault:` slugs in `canon.md` and `checks.md` are the titles of notes in my private notes vault. They aren't links you can follow, but each title states the claim it stands for.
- The Gate 0 and compliance checks lean toward supplement and health copy (DSHEA, NZ DSR 1985, Canadian NPN, FTC substantiation), because that's what it was built on. The other checks are general.
