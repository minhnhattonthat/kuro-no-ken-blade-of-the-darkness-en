-- Warp to a scene from a cold boot (docs/re/scenes.md). Run with tools/routes/boot.txt (title -> NEW GAME):
--   emu.py rom.cue --out work/qa/warp --route tools/routes/boot.txt --script tools/debug/warp.lua
--          --var "SCENE='06blk_1'" --frames 40000      (or --state-in work/states/base_<cue>.sstate, no route)
-- How: after the new-game intro (see below), we set var 3 (destination area) so the area script leaves through
-- the game's own area change, holding the scene's variables and flags until the target loads. Scene options
-- (scenes.lua): pos, keys, mash, shots, run/inject (start a shop, fight or VIS from the idle loop), map/event.
-- Globals: SCENE (name in scenes.lua, or "list" to log all names), SETTLE (frames from the load to the proof
-- shot, default 600), POS = {x, y}, STATE (savestate written at the proof), BASE (savestate at the intro's end),
-- KEEP=1 (run on to --frames). Log lines: "warp <scene>: area .. loaded", "slots a|b|c", "proof ok|FAIL ...".
local mem = PCSX.getMemPtr()
local function rd(a) return mem[a % 0x200000] end
local function wr(a, v) mem[a % 0x200000] = v end
local function cstr(a, n)
  local t = {}
  for i = 0, (n or 16) - 1 do local c = rd(a + i); if c == 0 then break end; t[#t + 1] = string.char(c) end
  return table.concat(t)
end
-- script variables: u16 at 0x80094120 + 2*i; bit flags at 0x80094340 (flag n = byte n>>3, bit n&7)
local function setvar(i, v) wr(0x80094120 + 2 * i, v % 256); wr(0x80094121 + 2 * i, math.floor(v / 256) % 256) end
local function getvar(i) return rd(0x80094120 + 2 * i) + rd(0x80094121 + 2 * i) * 256 end
local function setflag(n, on)
  local a = 0x80094340 + math.floor(n / 8)
  local bit = 2 ^ (n % 8)
  local v, has = rd(a), (rd(a) % (2 * bit) >= bit)
  if on and on ~= 0 then if not has then v = v + bit end elseif has then v = v - bit end
  wr(a, v)
end
local function setpos(x, y)   -- player object 0 at 0x80094df8 (86-byte objects): +4 x, +6 y, copies at +8/+0a
  for _, o in ipairs({ 4, 8 }) do
    wr(0x80094df8 + o, x % 256); wr(0x80094df9 + o, math.floor(x / 256))
    wr(0x80094dfa + o, y % 256); wr(0x80094dfb + o, math.floor(y / 256))
  end
end

-- the emulator's working folder is tools/pcsx/, so repo files are ../debug/...
local SC = dofile("../debug/scenes.lua")
local D = SC.data
if SCENE == "list" then   -- tour.py: log every scene name in order
  for _, name in ipairs(SC.order) do L.log("scene " .. name) end
  L.finish(0)
  return
end
local sc = SC.scenes[SCENE] or error("unknown SCENE " .. tostring(SCENE) .. " (see tools/debug/scenes.lua)")
-- TEXT: show that string in a field message box instead of running the scene's own script (op 0x3b, inline text).
-- Use it for font sheets and the width gate: --var "TEXT='ABCabc 0123 (every printable ASCII)'".
if TEXT and TEXT ~= "" then
  local bytes = { 0x3b, 0x02 }
  for i = 1, #TEXT do bytes[#bytes + 1] = TEXT:byte(i) end
  bytes[#bytes + 1] = 0
  sc.run, sc.inject, sc.mash = true, bytes, sc.mash or 30
end
-- RUN: run that script address instead of the scene's (see the `run` block below), e.g. --var "RUN=0x5057".
if RUN then sc.run = RUN end
-- PATCH: extra bytecode patches, "script:address:hexbytes" separated by ';' (see the patches block below).
if PATCH and PATCH ~= "" then
  sc.patches = sc.patches or {}
  for step in PATCH:gmatch("[^;]+") do
    local name, at, hex = step:match("^%s*([^:]+):(%x+):(%x+)")
    assert(name, "PATCH step needs script:address:hexbytes, got " .. step)
    local bytes = {}
    for i = 1, #hex, 2 do bytes[#bytes + 1] = tonumber(hex:sub(i, i + 1), 16) end
    sc.patches[#sc.patches + 1] = { script = name, at = tonumber(at, 16), bytes = bytes }
  end
end
local SLOT = { 0x800ce2a8, 0x800ce2b8, 0x800ce2c8 }   -- names in script slots 0 (area), 1 (map), 2 (event)
local MAP = 0x800953e0               -- current map (BEP) name, e.g. "blk1"
local area = sc.area
assert(#area == 5, "area names are 5 characters")
local function slot(i) return (cstr(SLOT[i]):lower():gsub("%.scn$", "")) end

local state, loaded_at, last, skip_at, intro = "wait", nil, "", nil, false
-- The new game's first entry to 02OLB and its intro set up the party and the field; warping before that leaves
-- maps without the player (or garbled). So we play the intro, then leave 02OLB. BASE = path: save a state there
-- (tour.py makes one per run and starts every scene from it with --state-in and STATE_IN=1).
local hop = area == "02olb" and "01fld" or area   -- 02OLB can't be left for itself: go through the world map
L.on_frame(function(n)
  if sc.frame_fn then sc.frame_fn(n, mem) end
  if state == "wait" then
    -- the intro event 02olb00a (VIS 0 and 2, ~20000 frames) must play: it finishes the field set-up, and
    -- skipping it leaves garbled maps. Page through it; it hands over to 02olb01a in Ace's room.
    if slot(3) == "02olb00a" then intro = true end
    if L.route_done() and n % 20 == 0 then L.press("circle", 6) end
    if (intro or STATE_IN) and slot(1) == "02olb" and slot(3) == "02olb01a" then state, skip_at = "skip", n end
  elseif state == "skip" then
    if n == skip_at + 300 then
      if BASE then L.save_state(BASE); L.log("base state " .. BASE .. " at frame " .. n) end
      state = "go"
    end
  end
  if state == "go" then
    -- vars 0-3 are an area history: var 3 = destination; every area script leaves (99CMN 0x4000) once var 3
    -- isn't its own number, and the change (99CMN 0x4630) shifts var1=var2, var2=var3 and loads the area table
    -- entry var 2. So var 2 before it becomes var 1 = "came from".
    if hop ~= area and slot(1) == hop then hop = area end
    setvar(2, hop == area and (sc.from or 1) or 2); setvar(3, tonumber(hop:sub(1, 2)))
    setvar(4, 0)   -- entrance 0 (the intro leaves 1 = Ace's room); a scene's vars can set another
    for k, v in pairs(sc.vars or {}) do setvar(k, v) end
    for k, v in pairs(sc.flags or {}) do setflag(k, v) end
    if slot(1) == area and hop == area then
        state, loaded_at = "loaded", n
        local vs = {}
        for k, _ in pairs(sc.vars or {}) do vs[#vs + 1] = string.format("v%x=%d", k, getvar(k)) end
        L.log(string.format("warp %s: area %s loaded at frame %d %s", SCENE, area, n, table.concat(vs, " ")))
    end
  elseif state == "loaded" then
    -- mash = N: press circle (confirm) every N frames until the proof shot, to page through text
    if sc.mash and L.route_done() and n < loaded_at + (SETTLE or sc.settle or 600) - 30 then
      L.press("circle", 6); L.press("-", sc.mash - 6)
    end
    local s = slot(1) .. "|" .. slot(2) .. "|" .. slot(3)
    if s ~= last then L.log(n .. " slots " .. s); last = s end
    if sc.shots and (n - loaded_at) % sc.shots == 0 then L.shot(string.format("w%06d.png", n)) end
    -- keys = "FRAMES BUTTONS;..." (route syntax) pressed from keys_at frames after the load (menus, shops)
    if sc.keys and n == loaded_at + (sc.keys_at or 420) then
      for step in sc.keys:gmatch("[^;]+") do
        local f, b = step:match("^%s*(%d+)%s+(%S+)")
        L.press(b, tonumber(f))
      end
    end
    -- patches: rewrite bytecode once its script is loaded (RAM = 0x80168000 + address), e.g. the VIS index of
    -- an ff 27 op. Scene field patch = one {script, at, bytes}; PATCH adds more without editing scenes.lua:
    --   --var "PATCH='02olb:0000:065700;02olb:0059:41424300'"   (script:address:hexbytes, ';' between patches)
    -- A script can be reloaded (the map script is, when a shop starts), so they are re-applied for PATCH_FOR
    -- frames from loaded_at + PATCH_AT (default 0..400).
    local plist = sc.patches or {}
    if sc.patch then plist[#plist + 1] = sc.patch end
    local pa, pf = PATCH_AT or 0, PATCH_FOR or 400
    for _, p in ipairs(plist) do
      if n >= loaded_at + pa and n <= loaded_at + pa + pf
         and (slot(1) == p.script or slot(2) == p.script or slot(3) == p.script) then
        for i, v in ipairs(p.bytes) do wr(0x80168000 + p.at + i - 1, v) end
        if not p.done then
          p.done = true
          L.log(string.format("%d patched %s %04x (%d bytes)", n, p.script, p.at, #p.bytes))
        end
      end
    end
    -- run = script address: make the area's idle loop (`55 0f w3 w<area> w<loop>`, wait a frame while var 3 is
    -- this area) jump there, to start a shop or a scripted battle (5f bg, 7f data, 81 var) without walking to it
    if sc.run and n == loaded_at + (sc.run_at or 400) then
      -- (else the first `55 06 <loop>`). A thread waiting on 55 resumes at the next op, so that op becomes
      -- `06 <run>`. Script threads are cooperative; only one loop is patched so only one thread runs it.
      local num, hit, alt = tonumber(area:sub(1, 2)), nil, nil
      for a = 0, 0x1ff8 do
        local b = 0x80168000 + a
        if rd(b) == 0x55 and rd(b + 1) == 0x0f and rd(b + 2) == 3 and rd(b + 3) == 0 and rd(b + 4) == num
           and rd(b + 5) == 0 and a - (rd(b + 6) + rd(b + 7) * 256) >= 0
           and a - (rd(b + 6) + rd(b + 7) * 256) < 16 then hit = a; break end   -- loops back to itself
        if not alt and rd(b) == 0x55 and rd(b + 1) == 0x06 and rd(b + 2) + rd(b + 3) * 256 == a then alt = a end
      end
      hit = hit or alt
      -- run = true with inject = {bytes}: put those ops there instead (e.g. ff 27 00 <vis> 00 03 = play a VIS)
      -- (followed by a jump back to the loop's 55)
      local code = sc.inject or { 0x06, sc.run % 256, math.floor(sc.run / 256) }
      if hit then
        if sc.inject then
          code = {}
          for _, v in ipairs(sc.inject) do code[#code + 1] = v end
          for _, v in ipairs({ 0x06, hit % 256, math.floor(hit / 256) }) do code[#code + 1] = v end
        end
        for i, v in ipairs(code) do wr(0x80168000 + hit + i, v) end
      end
      L.log(string.format("%d run %s via loop %s", n, tostring(sc.run), hit and string.format("%04x", hit) or "NOT FOUND"))
    end
    -- the game places the player by entrance (var 4); pos = {x, y} or "zone" (first registered zone) overrides.
    -- shortcut: the camera doesn't follow a written position (found 2026-11-01); a real entrance var per area
    -- would fix the view, find it when a chapter's QA needs it
    if (POS or sc.pos) and n == loaded_at + (sc.pos_at or 300) then   -- the map loads ~200 frames after the area
      local pos = POS or type(sc.pos) == "table" and sc.pos or nil
      if not pos then   -- first zone the map script registers that the loaded map defines
        local m = cstr(MAP)
        for _, id in ipairs(D.zones[slot(2)] or D.zones[slot(1)] or {}) do
          if D.eve[m] and D.eve[m][id] then pos = D.eve[m][id]; break end
        end
        if not pos and D.eve[m] then   -- else the map's lowest zone
          for id = 0, 63 do if D.eve[m][id] then pos = D.eve[m][id]; break end end
        end
      end
      if pos then setpos(pos[1], pos[2]); L.log(string.format("%d map %s pos %d,%d", n, cstr(MAP), pos[1], pos[2])) end
    end
    if n == loaded_at + (SETTLE or sc.settle or 600) then
      L.shot("proof.png")
      -- ok: the area is still loaded with a map (BEP), and the scene's expected map/event scripts if it names them
      local ok = slot(1) == area and (sc.map == false or cstr(MAP) ~= "") and (not sc.map or slot(2) == sc.map)
                 and (not sc.event or slot(3) == sc.event)
      L.log(string.format("proof %s at frame %d slots %s map %s", ok and "ok" or "FAIL", n, s, cstr(MAP)))
      if STATE then L.save_state(STATE) end
      if not KEEP then L.finish(ok and 0 or 3) end   -- KEEP=1 keeps running to --frames
    end
  end
end)
