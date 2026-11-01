-- Recon probe: log the three script-slot names and the area number whenever they change.
-- Slots (docs/re/scenes.md): names at 0x800ce2a8/b8/c8 (16 bytes each), area number u16 at 0x80094336.
-- --var DUMP_AT=N dumps main RAM at frame N (ram_N.bin in --out).
local mem = PCSX.getMemPtr()
local function cstr(a)
  local t = {}
  for i = 0, 15 do
    local c = mem[(a + i) % 0x200000]
    if c == 0 then break end
    t[#t + 1] = string.char(c)
  end
  return table.concat(t)
end
local function u16(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 end
local last = ""
L.on_frame(function(n)
  local s = string.format("%s|%s|%s area=%d", cstr(0xce2a8), cstr(0xce2b8), cstr(0xce2c8), u16(0x94336))
  if s ~= last then L.log(n .. " " .. s); last = s; L.shot(string.format("s%06d.png", n)) end
  if DUMP_AT and n == DUMP_AT then L.dump_ram(string.format("ram_%06d.bin", n)) end
end)
