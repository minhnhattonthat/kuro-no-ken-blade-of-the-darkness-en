-- Recon probe: dump the 12x12 4bpp glyph bitmaps the text renderer hands to the GPU, with each one's char code
-- (emulator: needs emu.py --debugger).
--   0x80050908? no: 0x80050508 = glyph draw entry ($a0 = char code) -> remember the code
--   0x800506f0 = addiu $a0, $sp, 0x10 just before the sprite emit -> dump bytes at $sp+0x10
-- Output: "glyph <frame> <code:04x> <96 bytes hex>"
local mem = PCSX.getMemPtr()
local from, to = FROM or 0, TO or 1e9
local maxn = GLYPH_MAX or 200
local count, code = 0, 0

L.on_exec(0x80050508, function()
  code = PCSX.getRegisters().GPR.n.a0 % 0x10000
end)

L.on_exec(0x800506f0, function()
  if L.frame < from or L.frame > to then return end
  if count >= maxn then return end
  count = count + 1
  local sp = PCSX.getRegisters().GPR.n.sp
  local out = {}
  for i = 0, 95 do out[#out + 1] = string.format("%02x", mem[(sp + 0x10 + i) % 0x200000]) end
  L.log(string.format("glyph %d %04x %s", L.frame, code, table.concat(out)))
end)

L.on_frame(function(n)
  if n == to and to < 1e8 then L.log("glyph total " .. count) end
end)
