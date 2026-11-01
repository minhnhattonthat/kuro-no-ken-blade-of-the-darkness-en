-- Recon probe (needs --debugger): log writes to the player object's x/y (0x80094dfc..0x80094dff) with the PC,
-- the current script address (word at 0x80088fd4 minus 0x80168000) and the value written; distinct (pc, script) pairs.
local mem = PCSX.getMemPtr()
local seen = {}
-- WATCH = {lo, hi} watches another range.
L.on_write((WATCH or {})[1] or 0x80094dfc, (WATCH or {})[2] or 0x80094dff, function(addr, width)
  local pc = L.pc()
  local p = mem[0x88fd4] + mem[0x88fd5] * 256 + mem[0x88fd6] * 65536
  local key = string.format("%08x %05x", pc, (p - 0x168000) % 0x1000000)
  if not seen[key] then
    seen[key] = true
    L.log(string.format("%d pc=%08x scr=%05x addr=%08x", L.frame, pc, (p - 0x168000) % 0x1000000, addr))
  end
end)
local last = ""
L.on_frame(function(n)
  local s = string.format("x=%d y=%d", mem[0x94dfc] + mem[0x94dfd] * 256, mem[0x94dfe] + mem[0x94dff] * 256)
  if s ~= last then if n % 10 == 0 then L.log(n .. " " .. s); last = s end end
end)
