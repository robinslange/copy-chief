# AI tells

V4's detector. These are constructions that mark a draft as machine-written
regardless of whether the claim underneath is true. Check the draft against
every section below; one match is a finding.

## Em dashes and en dashes

Banned, absolutely, in copy. No exemption.

The source is `brain/_system/persona.md`: "No filler. No preamble. No em
dashes, no en dashes." That rule is hook-enforced at write time in the
vault: an explicit instruction, not a prevalence claim, and it does not
need a headcount across the vault to be binding here.

(A whole-vault count would in fact run the other way: the dash shows up in
roughly a fifth of notes vault-wide, concentrated in older and
externally-sourced material. 0-inbox, the folder the write-time hook
actually gates, runs lowest, which reads as the hook holding going forward
rather than retroactively. That pattern is suggestive, not proof, and the
rule doesn't rest on it.)

The vault carves out one exemption, for Source: and Related: lines, where
the dash is a structural separator rather than a piece of prose. Marketing
copy has no Source: or Related: line. There is no structural use for the
dash to hide behind, so in copy the rule is absolute.

This isn't only a borrowed house rule. Em-dash density is independently
one of the most recognised signatures of machine-written prose, the
mark of a sentence reaching for a pause it hasn't earned with structure.
The two reasons point the same direction, which is why this section
leads the file.

Rewrite the sentence instead of trading the dash for a comma in the same
slot. A comma inherits the dash's laziness; a period or a rebuilt clause
doesn't.

## Structural tells

- "It's not X, it's Y" or "It was never X, it was Y" as a closing move.
  Banned outright by the global CLAUDE.md engineering stance, which names
  this construction by name.
- Hedging theater: "It's worth noting that", "It's important to
  remember", "Arguably", or praising the question before answering it.
  Also named directly in the CLAUDE.md stance. Persona.md's own rule cuts
  the same way from the other side: "Uncertainty gets one line, not three
  hedging paragraphs."
- Tricolons built for cadence, not because there are three things to
  say ("better, faster, stronger" where two examples would have been
  honest, or four were available and got trimmed to fit the rhythm).
- "In a world where …" openings, and their relatives ("Imagine a world
  where", "What if I told you").
- A closing paragraph that restates what the reader just read instead of
  ending on the last new thing the copy has to say.
- Uniform sentence length across a passage with no short sentence to land
  on. This is the same failure V3 tests for on the whole body; V4 flags
  it as a voice tell where V3 flags it as a rhythm defect. Report it once,
  under whichever check you hit first.

## Lexical tells

- "delve", "leverage" as a verb, "robust", "seamless", "elevate",
  "unlock", "harness", "tapestry", "testament to", "game-changer".
- "Not only … but also" standing in for a plain "and".
- Performative bluntness: a sentence built to sound decisive rather than
  to state a decided thing. The CLAUDE.md stance calls this out as
  distinct from real plainness: earn the verdict with the evidence in
  the sentence, don't perform having one.

## What passes

A filter that only lists prohibitions teaches a writer to strip words out.
The positive version, from the same two sources:

- Compression. Say the thing once, in the fewest words that carry it, and
  cut the rest. Persona.md's iceberg rule: know more than you write, and
  let the reader feel what's under the surface rather than being told
  about it.
- A sentence that does work. Every sentence earns its place or it goes.
  No sentence that exists to sound like writing.
- One effect, decided before the first word, not a paragraph trying to
  land three different notes at once.
- Short sentences next to long ones, driven by the content, not by a
  rhythm imposed on it. A sentence ends where the thought ends.
- Concrete nouns and specific numbers over categories: "your legs are
  still heavy on Thursday", not "optimal recovery support".
- Plain observation, stated flat. Uncertainty gets one honest line, not a
  hedge.
- Active voice, present tense.
