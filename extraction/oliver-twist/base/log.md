# Extraction log: oliver-twist

The `extraction` workflow (§13.6) run on the `oliver-twist` base, chapters 1–12,
in a tool-using host: Claude Code in VS Code, playing each agent from its file in
`lorestore/agents/` at spec `v0.4`, and the human where the workflow asks for one.
Each step lists what it read, what it wrote, and anything the spec or the agent file
didn't settle. Findings for the spec are collected at the end.

## Before F0 (human)

- Wrote `package.yaml` (`status: open-for-extraction`, version 0.1.0, CC-BY-4.0) and
  `sources.md` with one source, `novel`, tier `primary`.
- Split the novel into 53 units, `texts/ot/ch01.md` to `ch53.md`.

## F0: ruler (worldbuilder)

- Read: `package.yaml`, a listing of `texts/`, `sources.md`.
- Wrote: `canon-timeline.md`, one work `OT` (`chapter › scene`), 53 chapters.
- No `## Dates`: the base declares no calendar. The novel never states a year.
- Gate (milestone): approved.

## F0b: seed roster (character-designer)

- Read: a listing of `texts/`. No cast list was given, deliberately, to test the file
  as written.
- Wrote: `characters/_roster.md` with one row, `oliver-twist`, from the work's title.
- **Finding 1.** In a base, F0b's reads (a file listing and an optional cast list)
  give it almost nothing: it can't open the texts, so without a human's cast list the
  seed holds only what the titles name. Every extractor then proposes the whole cast
  under `## New names`, independently, and F2a reconciles them. The step is close to a
  no-op unless a human supplies the cast; §13.6 could say so, or let F0b read the
  units' headings.
- Gate (milestone): approved.

## F1: extraction (extractor), chapters 1–12

- One extractor per unit, run one after another; each read only its own unit, the
  ruler, the seed roster, and `sources.md`, as the agent file says.
- Wrote: `extractions/ot/ch01.md` to `ch12.md`. Each opens with a `Scenes:` line that
  numbers the unit's scenes, since the ruler leaves scenes uncounted.
- Items for a human went under each record's `## Needs a human`. They're settled at the
  F2a gate below.
- ch11 was re-run after F2b's dry run (see F2b).

## F2a: roster (merger)

- Read: every record's `## New names`, the seed roster.
- Wrote: `characters/_roster.md`, 38 rows, all `origin: canon`, aliases joined with `; `.
- Gate (milestone): the `Needs a human` items, settled as follows. These are Claude's
  calls, standing in for the human; each is marked for Sam to confirm.
  - **`bookstall-gentleman` and `mr-brownlow` are one man** (ch10, ch11). The merger's
    rule is to keep the existing slug and record the new one as its alias, which would
    keep `bookstall-gentleman`. The gate chose `mr-brownlow` instead, and recorded
    `bookstall-gentleman` as its alias. *Confirm.*
  - "Mrs. Thingummy" (ch01) is the surgeon's stand-in, not a name: no alias. *Confirm.*
  - Fagin: the narrator's epithet "the Jew" is not recorded as an alias. The characters
    call him Fagin, and Dickens cut the epithet in 1867. "the merry old gentleman" is.
    *Confirm.*
  - "Tom White" (ch11) is not an alias. *Confirm.*
  - Trip, the Sowerberrys' dog, gets a roster row (ch04). *Confirm.*
  - The "porochial surgeon" of ch05 is `parish-surgeon`, as the record filed him.
    *Confirm.*
  - The Baytons share the surname on the coffin order (ch05). *Confirm.*
  - `bill-grave-digger` has a roster row but no facts, so no sheet.
  - The other items (dating, rumors, beliefs, foreshadowing, modules) are findings for
    the spec, not roster decisions; they're listed below.

## F2b: per-target merge (merger)

- 43 targets: 37 character sheets, `places.md`, `society.md`, `relationships.md`,
  `knowledge.md`, `glossary.md`, `quotations.md`. Run as one script applying the
  merger's rules (gather, map aliases, sort by point, merge exact duplicates, keep
  confirmations, flag conflicts, validate points, sources, slugs, and `True from`),
  rather than 43 separate agents. That script is now `tools/lx.py merge`, which
  reproduces this merge exactly. The results were then read by hand.
- The dry run found one conflict: Oliver's `standing` at OT:11:2 had two values, his
  committal and his discharge. Both happen in one scene of the ch11 record. Re-ran F1
  for ch11 with the hearing split into two scenes (OT:11:2 committal, OT:11:3
  discharge), as ch01 had been split at the mother's death. The merge then ran clean.
- Mappings used for files whose tables don't match the record's columns: see
  Findings 3 and 4.
- Quotation IDs are `<speaker>-<n>`, numbered in ruler order. The records carry no ID
  and no source column; the merger supplied both.
- No gate.

## F4: index (`indexer` skill)

- Wrote: `index.md`, every file with its layer from §3.3.
- The indexer is a skill with no reference file in `agents/`; it was run from §3.3 and
  §10.3.
- Gate (milestone): pending Sam's review. Version stays 0.1.0, status
  `open-for-extraction`: chapters 13–53 aren't extracted.

## Findings

Numbered for issues against 0.5. Chapter references are to the records where each
came up.

1. **F0b in a base** (above): without a cast list it seeds only the title character.
2. **Mid-scene changes.** Two values of one attribute at one point are a merge
   conflict. The extractor's file doesn't say so, and nothing tells it to split a scene
   where a value changes (ch01, ch11). A line in §12 for the extractor would catch it
   before F2b.
3. **The record's columns don't fit every target.** `glossary.md` (`Term | Meaning |
   Kind`) and `knowledge.md` (`## Secrets` with no `As of`, `## Knowledge` keyed by
   character) needed ad hoc mappings: Entity = term, Attribute = kind, Value = meaning;
   Entity = secret, Attribute = `truth` or `state:<slug>` (ch08, ch09). §10.6 could
   define them.
4. **`quotations.md` needs an `ID` and a `Source`**, which the record's
   `## Quotations` table lacks. The merger made them up.
5. **Cumulative attributes.** A state history replaces a value with the next, so rows
   that add to a thing (a shop's rooms, a gang's members, a boy's possessions) either
   repeat everything or lose the earlier part at a snapshot. The records wrote deltas
   ("adds a back kitchen"), which the snapshot gets wrong. Either extractors should
   restate the whole value, or the format needs a way to add.
6. **Free-form attribute names drift** between extractors working in parallel:
   `appearance` vs `dress` (ch04), `standing` vs `status`, `opinion-of-…` vs
   `impression-of-…` vs `belief-about-…`. Nothing lists the names a base uses. A
   per-package attribute list, or the glossary, could.
7. **No calendar.** Spans (nine years at the farm), ages (nine, then ten), seasons
   (winter), and weekdays can only be values (ch02, ch05, ch08, ch11). And
   `history.md` requires a `date` row on every event, so a world with no calendar
   can't have a history (ch04).
8. **Summary scenes.** A scene that covers years was dated at the scene that first
   shows the state, with `True from` set to the summary's point (ch02). §4 describes
   `True from` for revealed backstory; it should say whether this use is right.
9. **Flashbacks within a unit.** Scenes 3 and 4 of ch12 tell events from OT:10:3. They
   were dated where they're told. §6.8 covers order inversions in a project; it
   doesn't say how an extractor dates a flashback in canon.
10. **Narrator's foreshadowing** ("in all his after life", ch07) has no place to go: a
    fact about the future, stated now.
11. **Rumor and belief.** A rumor the narrator reports (ch03) and what a character is
    told about another (ch06) were recorded as a belief on the believer's sheet, not as
    fact on the subject's. The agent files don't say which.
12. **Cross-unit identity.** An unnamed character named in a later unit
    (`bookstall-gentleman` → `mr-brownlow`) is caught only if someone at F2a reads the
    records' contexts. The merger's rule keeps the earlier, worse slug, and puts a slug
    in the `Aliases` column, which §10.9 defines as names.
13. **Narrator's epithets.** An epithet the narrator uses but no character does ("the
    Jew") isn't an alias in the §10.9 sense, and there's no column for it.
14. **Modules.** The walk to London is travel data (distances, days), but the base
    doesn't enable travel (ch08). The extractor can't propose a module.
15. **Animals and objects.** A named dog went in the roster (ch04). A portrait that
    matters to the plot (ch12) has nowhere to go but a place's description.
16. **Town entities.** One record put the town's namelessness on `workhouse`, another
    created `town` (ch01, ch06). The merger can't merge entities with different ids.
17. **The indexer has no reference file**, unlike the other §13.6 steps.
18. **No validator for a user's package.** `tools/check.py` checks only the spec's own
    examples, so the merged files here were checked only by the merge script.
19. **Character sheets from extraction** have no `## Voice signature`, `## Wants and
    needs`, or `## Arc`, which §10.5 says they SHOULD have. No step in §13.6 writes
    them.
