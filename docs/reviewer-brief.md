# Translation reviewer brief - Kuro no Ken: Blade of the Darkness

You review one or more batches of a JP->English fan translation. Read-only: no edits, no git, no subagents.
Mechanical validity (ids, codes, ASCII, page count, glossary spellings) is already enforced by
`tools/batches.py check` - judge translation quality. Return the report as your final message: the controller saves it.

## Inputs (paths in your dispatch)
- Pairs files `work/tl/<batch>.pairs.txt`: every unit as `>> id | speaker | form | JP` then `EN: ...`, in story
  order (neighbours are the context). JP `/` = the JP's own line breaks (they split words; ignore them). A `cont`
  unit is the next page of the previous unit's speech. Read ALL of each file.
- `glossary.md` (rulings at the top), `docs/style-reference.md` (voices), `docs/synopsis.md` (who is who, reveals).

## Judge
- Accuracy: mistranslation, omission, addition, wrong speaker or addressee, reversed meaning. Quote the JP and say
  what it means.
- Consistency: glossary names/terms exactly; honorifics kept (-san, -sama) and stable within a scene; the same
  repeated NPC line translated the same way.
- Things players caught that reviewers missed: jokes/wordplay losing their punch; ordinal suffix after a variable;
  abbreviated names or terms; awkward stock phrases ("... GET!").
- Voice: each speaker against their row in the style reference. Register markers flatten most often: old-man
  じゃ/のう/わし, rough ぜ/ねぇ/てめえ, feminine かしら/わよ/のね, Zephudol's slurring, Hiko's archaic grandeur,
  Melfina's ですの, the Mayor's passive aggression. A line any speaker could have said is Important.
- Spoilers: a line must not reveal more than the JP does at that point (Vii, Hiko, the Apostles).
- Naturalness: would a fan-translation reader stumble?

## Report
### Issues
#### Critical (meaning reversed, wrong speaker, broken text)
#### Important (clear mistranslation, glossary inconsistency, abbreviation, a character's voice flattened, joke dead)
#### Minor (style - deferred to one polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
Per batch: `bNNN: Approved | Needs fixes - one sentence why.`
