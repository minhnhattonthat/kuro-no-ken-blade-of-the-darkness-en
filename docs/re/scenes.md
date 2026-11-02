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

## BSX battle talk (decoded 2026-11-02; seen in-game, scenes `battle_talk` + `battle_talk_party`)
The talk lines are run by the **battle AI interpreter** (0x8003c8f4). A BSX's header holds u16 offsets (C021_X10:
0x10-0x27, 12 slots) of AI records; a record is `<b0> <b1> <op>` + args, `cb 90` = empty, and the talk blocks are
records `fb fa <op>` whose op handler (table 0x80010934) tests a battle condition and then calls the **talk
sub-interpreter 0x8003c4a0** (table 0x80010914) on the args. Talk ops: `00` end, `01 <u8>` nonzero = later `03`s
use window slot +2, `02 <u16> <u16>` the two voice/portrait names (file offsets, e.g. 0x79f `zefy_m5`, 0x6c4 `kies_m5`; 0
= none) -> gp+0xd00 / gp+0xd7c, `03 <side> <u16 record>` show a talk record (**4 bytes**: side 02/03 = which
name/portrait slot, then text via 0x800545c8; the handler does `s2 += 4`), `04 <n> <n x u16>` jump to entry
gp+0xcb0 of a table of n offsets (`gp+0xcb0 >= n` skips the op), `05 <u8>` 2 bytes (ff = none, else window effect),
`06 <u16>` 3-byte jump. gp = 0x800882dc. Byte lengths read off the dispatcher 0x8003c4a0 (op 03 `s2 += 4` at
0x8003c698, op 05 `s2 += 2` at 0x8003c724, op 06 `s2` = u16 + slot base at 0x8003c738).
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
**AI op 0 seen in-game 2026-11-02** (scene `battle_talk_party`, proof `work/qa/talkparty/proof.png`): the op-0
record (C021_X10 0x68e) is `fb fa 00` + a talk stream `04 04 9c06 a606 b006 ba06` - a 4-entry table picked by
gp+0xcb0 = `(h[0x8008905e] != 0) * 2 + byte[0x8007f5fc + u32[0x80088f70]]` (0x8003c950..0x8003c9b0), gated on
`h[0x8008905e] < 2` and `h[0x800890b8] == 5`. Entry 0 = names (none, `kies_m5`) + record 0x6d4 `B00000`, which
draws in the **right-hand** slot (side 03) with Caius' portrait: `Caius / "Looks like we can't escape..."`. Entry
1 = Caius 0x705, 2 = Shinobu 0x736, 3 = Shinobu 0x75d (`h[0x8008905e] = 1` picks 2 and 3).

### Talk refs (corrected 2026-11-02: they are talk op streams, no second reader)
Measured over `work/orig/mps/BSX/*.BSX`: **312 `03 <sub> <u16 record>` ops in 50 of the 274 files** (sub 0x02 in
93, 0x03 in 218, 0x01 in one; 49 files hold more than one - most `C021_X10` 28, `D010_X10` 22, `D060_S21` 17).
The byte after the u16 is the stream's next op - 0x00 end (233), 0x05 window effect (75), 0x06 jump (4) - not an
extra argument; op 03 is 4 bytes (see above).
They are grouped because they are the streams the AI ops run: a file's talk data starts after
`.. 90 fb fa 00 04 04 <4 x u16>` (the op-0 table `04 04 <4 offsets>`), and each entry is a talk stream
`02 <u16 name> <u16 name> 03 <side> <u16 record> [05 ff] 00`. In `C021_X10` the entries continue
`02 9f 07 c4 06` (`zefy_m5` + `kies_m5`) + `03 02 1f 09` + `00`, then `02 9f 07 00 00` + `03 02 4e 09` + `05 ff`,
...: op 02 sets the names, op 03 shows the record, `05 ff` clears the window effect, `00` ends the stream. So the AI
interpreter walks all of it (it hands the op 0/3/4 args to 0x8003c4a0) and there is no separate reader: the earlier
"second reader" search came from reading `03` as a 5-byte op.
Records reached only through an op-4 table (`03 03 <u16>` inside an entry) are translated as well: the insert maps
one English line per JP line across every file and rewrites every `03 <sub> <u16>` slot (B00000 above shows it
in-game). Still unseen in-game: AI op 4 (0x860), the "actor 0 at 0 HP" line - actor 0 is Kaies, who is not in this
fight, so it needs a fight he is in; the op-3 records and op-0 entries 1-3 use the same box and wrap.

## Other ops of note
- 0x80 (9 values): random-encounter setup for a map (table address, rate, ...; stored at 0x80095394..).
- 0x7d `u8, var, value`: choice menu; the chosen index goes to the var.
- ext 0x2e: picture sub-interpreter (credits `KRED*`, sub-op 2 `w w string` loads a picture).
- ext 0x20: jump table `u8 N, var, default, N x target`.
- 0x3b string: message line; 0x3c string: voice/XA cue id (`S02000`); 0x7f string: sound/voice file
  (`d\d010_x10`).
Full operand table: `tools/scn.py` (`check` walks all 218 SCN with clean control flow).
