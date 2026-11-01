# Story reviewer brief - Kuro no Ken: Blade of the Darkness (PS1)

You read one chapter of a JP->English fan translation straight through, in story order, the way a player
meets it. Per-batch reviewers already judged single lines with +-2 lines of context; your job is what they can't see.
Read-only: no edits, no git, no subagents. Return the report as your final message; the controller saves it.

## Inputs (paths in your dispatch)
- Chapter file (`work/qa/story/chapters/<chapter>.txt`): every line of the chapter in script-file order, `>> id |
  speaker | JP` then the English on the next line. Read ALL of it, in passes if large, before judging.
  - One unit = one message page; ` / ` in the JP is a display line break. An empty English line under a unit whose
    JP continues the previous box is normal (the English paragraph sits in the box's first unit).
  - Files are in name order (area, map, event letter), close to but not exactly story order:
    `docs/synopsis.md` "Reconstructed chronology" has the real order. Several files are alternative versions of the
    same NPC line per story stage; repeated lines are expected.
- `docs/synopsis.md` (plot, who is who, late reveals), `docs/style-reference.md` (voice per character),
  `glossary.md` (rulings at the top; names are binding).

## Judge, across the whole chapter
- Continuity: each line follows from the one before; setups, callbacks and references back are kept; who knows what
  stays coherent; nothing gives a later reveal away early.
- Voice: each character sounds like the same person all chapter and matches their style-reference row: speech quirks,
  register, how they address others (Caius terse, Shinobu teasing, etc.). Name the line where a voice drifts or goes
  neutral.
- Emotion: anger, fear, grief and comedy beats are as strong as the Japanese; a running gag keeps its punchline.
- Accuracy only where a line breaks one of the above; single-line accuracy was reviewed already.
- Also flag: a name spelled differently from glossary.md, stock-phrase English ("GET!"), ordinals ("1th").
- Box limits are already enforced by tools; don't suggest longer text for its own sake.

## Report
### Issues
#### Critical (continuity break, reveal given away, wrong speaker)
#### Important (voice drift or flattened, emotional beat lost, setup or callback dropped, joke dead)
#### Minor (deferred to the polish pass)
Each: `id - JP gist - problem - suggested EN`.
### Assessment
`ok` (no Critical/Important) | `issue` - one sentence why. The controller writes this word into the chapter's verdict.
