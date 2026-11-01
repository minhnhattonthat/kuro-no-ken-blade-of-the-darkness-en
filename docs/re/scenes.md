# Scenes, script slots, variables (phase 2 debug tool)

Addresses for the pinned dump. **verified** = seen working in `tools/debug/warp.lua` runs (proof shots in
`work/qa/tour/`) or by disassembly; **guess** = not yet tested.

## Script memory and slots (verified, disassembly of 0x8002c748 + RAM dumps)
Script address space is u16, RAM = 0x80168000 + address (0x8002bb14).

| Slot | Address | Max size | Holds | Name buffer |
|---|---|---|---|---|
| 0 | 0x0000 | 0x2000 | area dispatcher (`02OLB.SCN`) | 0x800ce2a8 |
| 1 | 0x2000 | 0x2000 | map script (`02OLB01`, `03YSK01A`) | 0x800ce2b8 |
| - | 0x4000 | 0x1000 | `99CMN.SCN` common library, resident (loaded by the EXE, name at 0x8007f49c) | |
| 2 | 0x5000 | ? | event script (`02OLB01A`) | 0x800ce2c8 |

- Op 0x36 `value slot, string name` loads a SCN into slot 0x2000 or 0x5000 (skips if the name is unchanged).
  Op 0x35 `string` = **area change**: clears all three names, loads the area into slot 0, jumps to 0x0000,
  stores the area number (first two digits) in var 0x10b (u16 at 0x80094336). It never returns.
- Load path: file read to 0x80100000 (CdSearchFile in SCN.MPS), name copied, then memcpy to the slot.
- Phase 5 constraint: slot 1 holds 8 KB, 99CMN 4 KB. Largest SCN: 25TOU (12,923 B, slot 0, 8 KB?? see below).
  **Open:** 25TOU is an area script larger than 0x2000; it must spill into slot 1's space (25TOU loads no map
  script). Check before growing any SCN.
- The current map (BEP) name is at 0x800953e0 (`blk1`), set by op 0x5d `string 'd\blk1', 4 values`.
  BOD data of the loaded map at 0x80171800.

## Variables and flags (verified)
- u16 variables at 0x80094120 + 2*i (i < 0x110); bit flags from 0x80094340 (flag n = byte n>>3, bit n&7).
- Vars 0-3: area history. Var 3 = destination; the area change (99CMN 0x4628) shifts var0=var1, var1=var2,
  var2=var3, then indexes the area table with var 2. After it, var 3 = var 2 = current area, var 1 = previous.
  Every area script checks var 3 == own number and leaves (to 99CMN 0x4000) otherwise.
- Var 4: entrance / door number used by map scripts' entry switches (`08 4 ...`). Var 0x7e/0x7f: scratch.
- Var 0x82+N: area N's progress counter; the dispatcher picks the map and event script from it
  (`02OLB`: var 0x84 0 -> 02olb01 + 02olb01a, 1 -> 02olb01 + 02olb01b, 2 -> 02olb02 + 02olb02a ...).
  06BLK, 07CSL, 17DRL, 23SOH: low byte = district (switch), high byte = story stage (second switch).
- Flag 2: "in game". Clear on a new game: area scripts then take their first-entry path. Set by every area
  script after entry.
- Area table: 99CMN 0x4677, 7 bytes per area: name[5] NUL, byte (guess: chapter/disc music). Index = area
  number. Includes `77bug` and `78dmy` with no SCN file (removed debug area).

## How the warp enters an area (verified)
- The new game's first 02OLB entry (flag 2 clear) and the intro event 02OLB00A (VIS 0 and 2) set up the party
  objects and the field. Warping before the intro ends gives maps with no player sprite (objects 1+ empty) or
  garbled tiles; jumping over the intro (02OLB 0x23b) also garbles. So warp.lua plays the intro (circle every
  20 frames, ~18000 frames from power-on) until slot 2 holds 02olb01a, then sets var 2 = came-from, var 3 =
  target: the area's idle loop (`55 0f w3 w<area> w<loop>`) sees var 3 changed and leaves through 99CMN's area
  change. 02OLB targets hop through 01FLD first. Var 4 (entrance) is set to 0: the dispatcher's entrance
  table (`03 4 ...` in 02OLB at 0x1a0) does nothing for 0, so the player keeps the coordinates of Ace's room
  and some maps open on an empty corner (02OLB: the dock; 05SKS: black). Writing the player's x/y does not
  move the camera. **Open:** find each area's world-map entrance value (01FLD zone handlers, 99CMN 0x4e8 /
  0x11ee) when a chapter's QA needs the right view.
- Script threads are cooperative: a thread waiting on op 0x55 resumes at the next op. warp.lua's `run`/`inject`
  writes `06 <addr>` (or injected ops) right after the idle loop's 55 to start a shop, fight or VIS.
- Map scripts start with a jump table (`06 <handler>` x N at 0x2000): talk/door handlers. 02OLB01:
  0x2045 -> 0x38d6 inn, 0x204b -> 0x39a0 item shop.
- Scripted fight: `5f 'd\bac_NN'` (background), `7f 'd\<enemy>_<x>'`, `81 var` (fight; result in var: 1 = lost?
  guess). Field menu: cross. Random encounters happen on dungeon maps (21KTI cave).
- **Open (phase 4):** 02OLB01 0x19db after the item-shop greeting decodes as `01 5206` + bytes `ff 5b ...`
  that are no op; the shop list format is not decoded. `scn.py check`: 17DRL04 has two jump targets
  (0x2cfd, 0x2cff) inside a run of `00 02` data (`tests/test_scn.py` allows it).

## Player and map positions (verified)
- Objects: 86-byte records from 0x80094df8 (0x8002c480: value * 86). Object 0 = Shinobu: +4 x, +6 y (copies
  at +8, +0a), same units as the map's event zones; +0x32.. sprite state (0xff once set up).
- BEP `.EVE`: u16 n1, u16 n2, then (n1 + n2) records of 6 u16: flag, x1, y1, x2, y2, zone id. The second table
  holds the zones that op 0x52 `id, type, handler` registers (door/talk triggers). Midpoints are walkable
  spots next to doors; `tools/debug/gen_scenes.py` exports them (warp.lua `pos = "zone"` uses them).

## Visual scenes (verified for 0, 2, 5)
- Ext op `ff 27 00 <index> 00 03` (value type 0 + u16 index, then type 3): plays visual scene `index` (functions table at 0x800810f4, 0x00-0x16;
  VIS*.CG pictures + VIS*.MES text, XA voice `DS_*`). The new-game intro (02OLB00A) plays 0 (ship), then 2
  (bedroom) at 0x5088.
- Callers (index: script): 1 31END, 2/0 02OLB00A, 3 07CSL01, 4 06BLK02, 5 07CSL, 6 06BLK, 7 15MKR02A,
  8 15MKR02C, 9 16MKI01B, a 27KKI01, b 07CSL04, c 09HIK01, d 25TOU, e 25TOU00C, f 10TNI02, 10 07CSL08,
  11 17DRL08A, 12 27KKI02, 15 07CSL04, 16 26KKR06. 0x13, 0x14: no direct caller found.

## Is a data block ever displayed? (probe, 2026-11-02)
Two recon probes answer "is this data used / shown" for any RAM block, e.g. the loaded BSX file at 0x80099170
(slot 0x1400). Both need `--debugger` (breakpoints run on the interpreter) and a `warp.lua` run:
- `tools/debug/slot_reads.lua` - every CPU read inside `SLOT..SLOT+SIZE-1`, as "frame offset pc", plus the ranges
  never read (vars `SLOT`, `SIZE`, `LEN` = the block's real length). Writes `OUT/slot_reads.txt`.
- `tools/debug/text_draws.lua` - every string the field/menu text layout 0x80051904 draws ("ptr caller text"), flags
  draws whose pointer is inside the block and draws containing `MARK` (default `ZQ`, the marker-build id prefix, so a
  copy out of the block is caught too). Writes `OUT/text_draws.txt`.
- Result for BSX: in a whole fight (scene `battle_boss`, which loads `D070_T10.BSX` = `D070_S10.BSX`, 721 bytes;
  party wiped, enemy acted several times) 202 of the file's 721 bytes were read but never 0x129-0x15b, the range
  holding its labels 呼ぶ (0x147) and 《相打ち》 (0x14c); the `CB 90` fill after the data is read at a 4-byte stride
  (0x8003c910) - it is the unused tail of the action-record array, not text. The layout drew 19 calls / 16 strings:
  the party name, HP/MP/ST, the 6 command names, the numbers and the game-over banner - nothing from the slot
  (`work/qa/bsxproof/`). The only other text path is the VIS caption renderer, which draws VIS*.MES
  (`docs/re/font.md`), not battle data. So the BSX action labels are editor documentation and stay Japanese (D14);
  the displayed names come from EXE (commands, labels), SMX (player arts, items) and SCN/MES.

## BSX battle talk (decoded 2026-11-02; seen in-game, scene `battle_talk`)
The talk lines are run by the **battle AI interpreter** (0x8003c8f4). A BSX's header holds u16 offsets (C021_X10:
0x10-0x27, 12 slots) of AI records; a record is `<b0> <b1> <op>` + args, `cb 90` = empty, and the talk blocks are
records `fb fa <op>` whose op handler (table 0x80010934) tests a battle condition and then calls the **talk
sub-interpreter 0x8003c4a0** (table 0x80010914) on the args. Talk ops: `00` end, `01 <u8>` nonzero = later `03`s
use window slot +2, `02 <u16> <u16>` the two voice/portrait names (file offsets, e.g. 0x79f `zefy_m5`, 0x6c4 `kies_m5`; 0
= none) -> gp+0xd00 / gp+0xd7c, `03 <side> <u16 record> <u8>` show a talk record (side 02/03 = which name/portrait
slot, then text via 0x800545c8), `04 <n> <n x u16>` jump to entry gp+0xcb0 of a list, `05 <u8>` (ff = none, else
window effect), `06 <u16>` jump. gp = 0x800882dc.
AI ops seen with talk (C021_X10, the Zephudol fight 06BLK04 0x32ba): op 0 (0x68e, 4 party lines, picked by
gp+0xcb0) needs h[0x8008905e] < 2 and h[0x800890b8] == 5; op 3 (0x792, Zephudol's "Not bad, huh?") needs
gp+0xc6e (0x80088f4a) == 1 and h[0x8008905e] == 3 (3 = the fight's running phase); op 4 (0x860) needs actor 0
(pointer table 0x80094dd8: party 0x800945f0 / 0x8009470c / 0x80094828, enemies 0x80094944..; u32 HP at +0x14) at
HP 0 - Kaies, who is not in this fight, so it can't fire here. gp+0xc6e is cleared at battle init (0x8003c1c8)
and set elsewhere (writer not found); the scene holds it at 1. Earlier runs saw no line because they pinned the
party's HP and never met a condition.
In-game (work/qa/talk4, tour_talk): name line + 3 rows on page 1, 4 rows a page, 25 columns from x 89; the page
mark sits in column 25 of a page's 4th row, so `insert.bsx_text` wraps that row at 24 (5 records had 25 there;
`tests/test_insert.py::test_bsx_text_keeps_the_page_mark_column_free`). Probe: `tools/debug/pin_hp.lua`.

### Talk refs (as first mapped)
Measured 2026-11-02 over `work/orig/mps/BSX/*.BSX` (recon script in `work/tmp/`, throwaway): **312 refs in 50 of the
274 files**, always `03 <sub> <u16 target>` whose target is a talk-record start (`01 42 <id5> 00`); sub is 0x02 in
93 refs, 0x03 in 218, 0x01 in one. 49 of the 50 files hold more than one ref (most: `C021_X10` 28, `D010_X10` 22,
`D060_S21` 17). The byte after the u16 is 0x00 (233), 0x05 (75) or 0x06 (4) - one more argument, meaning unknown
(a portrait/face id in the talk code is the likely one).
The refs are grouped, not scattered: each file has the refs after a shared header shape
`.. 90 fb fa 00 04 04 <u16> <u16> <u16> <u16> 00 02 00 00 <u16>`, and in `C021_X10` the entries continue
`02 <u16 ptr> <u16 value>` then `03 02 <u16 record> <u8>` then 0xff (entry separator), e.g. at 0x866:
`02 9f 07 c4 06` (0x79f = the file's own ASCII voice name `zefy_m5`) + `03 02 1f 09 00` (record 0x91f), and
`02 9f 07 00 00` + `03 02 4e 09 05`. So the table most likely reads "when <value> crosses <value in the 02 op>,
show this line" (0 = on death), but **the reader is not identified**: the AI interpreter at 0x8003c8f4 (sub-op
table 0x80010934, 50 entries, `cb` = end) cannot parse these entries - byte2 of `03 02 9f 07` would be 0x9f, out of
range - so a second, separate reader walks this data. `disasm.py xref` on the slot base 0x80099170 finds 7 sites
(0x8003052c, 0x80031bfc, 0x80031d88, 0x8003b82c, 0x8003dce4, 0x80048ee0, 0x80049588); 0x8003dce4 is the
interpreter's own end path, the others are unexamined.
Next step for the in-game look: find the reader there, then **patch the `02` value** in a fight (e.g. set 0x6c4 to
the boss's current HP) instead of fighting long enough to cross it - the earlier Zephudol runs (`docs/status.md`)
fought whole battles without a draw, which fits a value that never crossed rather than a missing code path.

## Other ops of note
- 0x80 (9 values): random-encounter setup for a map (table address, rate, ...; stored at 0x80095394..).
- 0x7d `u8, var, value`: choice menu; the chosen index goes to the var.
- ext 0x2e: picture sub-interpreter (credits `KRED*`, sub-op 2 `w w string` loads a picture).
- ext 0x20: jump table `u8 N, var, default, N x target`.
- 0x3b string: message line; 0x3c string: voice/XA cue id (`S02000`); 0x7f string: sound/voice file
  (`d\d010_x10`).
Full operand table: `tools/scn.py` (`check` walks all 218 SCN with clean control flow).
