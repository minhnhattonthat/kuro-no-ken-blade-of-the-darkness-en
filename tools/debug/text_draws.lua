-- Recon probe: which strings does the field/menu text layout (0x80051904) draw, and is any of them taken from a RAM
-- block we care about? Answers "is this data ever displayed": every field, menu and battle string goes through this
-- function (boxes, menus, the battle command window, HP/MP numbers, the game-over banner); the only other text path
-- is the VIS caption renderer (BIOS font, VIS*.MES, docs/re/font.md). Use it on a build where the block's text is
-- replaced by marker ids (build.py --marker writes `[id]`, a hand-made probe can write any MARK prefix).
--
-- Run with warp.lua (breakpoints need the interpreter: --debugger):
--   emu.py build/kuro_en.cue --state-in work/states/base_kuro_en.sstate --script tools/debug/warp.lua
--     --script tools/debug/text_draws.lua --var "SCENE='battle_boss'" --var "KEEP=1" --debugger --frames 2600
-- Vars: SLOT/SIZE = the RAM block to watch (default the loaded BSX file: 0x80099170, 0x1400); MARK = a text prefix
-- that means "this string came from the watched data" (default "ZQ"); the run's summary goes to OUT/text_draws.txt.
local SLOT = SLOT or 0x80099170
local SIZE = SIZE or 0x1400
local MARK = MARK or "ZQ"
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end
local function hexstr(a, n)   -- first n bytes of the string at a, as hex, stopping at NUL
  local t = {}
  for i = 0, n - 1 do
    local c = u8(a + i)
    if c == 0 then break end
    t[#t + 1] = string.format("%02x", c)
  end
  return table.concat(t)
end
local seen, order, calls, from_slot, marked = {}, {}, 0, 0, 0
L.on_exec(0x80051904, function()
  calls = calls + 1
  local r = PCSX.getRegisters().GPR.n
  local p = u32(r.a1 or 0)          -- the layout request's first word is the string pointer
  local ra = (r.ra or 0) % 0x100000000
  local s = hexstr(p, 32)
  local k = string.format("%08x %08x %s", p, ra, s)
  if not seen[k] then seen[k] = 0; order[#order + 1] = k end
  seen[k] = seen[k] + 1
  if p >= SLOT and p < SLOT + SIZE then
    from_slot = from_slot + 1
    L.log(string.format("SLOT DRAW frame %d: ptr %08x offset %04x caller %08x", L.frame, p, p - SLOT, ra))
  end
  -- the marker check also catches a copy: the bytes came from the watched block but the pointer did not
  local ascii = s:gsub("%x%x", function(b) local v = tonumber(b, 16); return (v >= 32 and v < 127) and string.char(v) or "." end)
  if ascii:find(MARK, 1, true) then
    marked = marked + 1
    L.log(string.format("MARK DRAW frame %d: ptr %08x caller %08x text %s", L.frame, p, ra, ascii))
  end
end)
L.on_frame(function(n)
  if FRAMES and n == FRAMES - 1 then
    table.sort(order)
    local out = { string.format("text draws %d, distinct strings %d, drawn from the watched block %d, with %q %d",
      calls, #order, from_slot, MARK, marked) }
    for _, k in ipairs(order) do out[#out + 1] = k .. " x" .. seen[k] end
    L.write_file("text_draws.txt", table.concat(out, "\n") .. "\n")
    L.log(out[1])
  end
end)
