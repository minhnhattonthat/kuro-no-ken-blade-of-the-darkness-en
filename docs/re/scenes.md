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

## Other ops of note
- 0x80 (9 values): random-encounter setup for a map (table address, rate, ...; stored at 0x80095394..).
- 0x7d `u8, var, value`: choice menu; the chosen index goes to the var.
- ext 0x2e: picture sub-interpreter (credits `KRED*`, sub-op 2 `w w string` loads a picture).
- ext 0x20: jump table `u8 N, var, default, N x target`.
- 0x3b string: message line; 0x3c string: voice/XA cue id (`S02000`); 0x7f string: sound/voice file
  (`d\d010_x10`).
Full operand table: `tools/scn.py` (`check` walks all 218 SCN with clean control flow).
