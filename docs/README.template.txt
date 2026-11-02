Kuro no Ken: Blade of the Darkness - English translation v{VERSION}
==================================================================

Unofficial English fan translation of Kuro no Ken: Blade of the Darkness (PlayStation, 1997, SLPS-01030). This package holds a patch only. You need your own dump of the Japanese disc; no game
data is included, and pre-patched images are not provided.

Translation status
------------------
Part of the game                                  Status
------------------------------------------------  -----------------------------------------------
Field dialogue, NPCs, events, signs, choices      English
Story cutscenes (VIS captions)                    English
Battle talk (boss and story fights)               English
Menus, status/equip/magic pages, shops, config    English
Items, equipment, magic, sword arts (names+desc)  English
Battle commands, messages, ailment markers        English (short forms: Fight, Magic, Po/Si/Se/Sl/Pa)
Opening prologue movie                            English subtitles (re-encoded)
Staff credits, save/load prompts                  English (redrawn pictures)
Title logo                                        Japanese logo kept (no official English logo)
Memory card file title (shown in the BIOS)        Japanese, as the game writes it

Base disc (must match)
----------------------
{HASHES}

Patching
--------
1. Use xdelta3 (command line) or Delta Patcher (GUI).
   xdelta3 -d -s "Kuro no Ken - Blade of the Darkness (Japan).bin" {PATCH} "Kuro no Ken (English).bin"
2. Copy your original .cue next to the patched .bin and change the file name inside it to the new .bin name.
   The patched image keeps the original single-track layout.
3. Start a new game (cold boot). A savestate made with the Japanese disc carries the old text pointers: load a
   memory card save instead.

Tested on PCSX-Redux (with the SCPH-5500 BIOS). Report problems (untranslated text, overflow, crashes) on the
project's GitHub issues page, with a memory card file if you can.

Notes
-----
- Honorifics are kept (-san, -sama); names are in Western order (given name first).
- In boss fights the Flee command is greyed out, as in the original.
- Translation and tooling were produced with AI assistance (Claude) and checked in the emulator.
- English text uses Terminus (bold 6x12); the redrawn credits use Liberation Sans (both SIL Open Font License 1.1).
- Kuro no Ken: Blade of the Darkness (c) its rights holders. This is a non-commercial fan work, not affiliated
  with them.
