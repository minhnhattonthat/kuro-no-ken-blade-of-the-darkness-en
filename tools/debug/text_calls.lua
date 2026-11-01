-- Recon probe: log each call of the field/menu text layout 0x80051904 with caller and args, and the string any
-- arg points at (first 12 bytes, hex). Once per (ra, string) so a redraw every frame logs once.
-- Use with warp.lua: emu.py ... --script tools/debug/warp.lua --script tools/debug/text_calls.lua
local mem = PCSX.getMemPtr()
local seen = {}
L.on_exec(0x80051904, function()
  local r = PCSX.getRegisters().GPR.n
  local args = { r.a0, r.a1, r.a2, r.a3 }
  local strs = {}
  for i, v in ipairs(args) do
    v = v % 0x100000000
    if v >= 0x80000000 and v < 0x80200000 then
      local s = {}
      for k = 0, 11 do s[#s + 1] = string.format("%02x", mem[(v + k) % 0x200000]) end
      strs[#strs + 1] = string.format("a%d->%s", i - 1, table.concat(s))
    end
  end
  local key = string.format("%08x %s", r.ra % 0x100000000, table.concat(strs, " "))
  if not seen[key] then
    seen[key] = true
    local sp = r.sp % 0x200000
    local st = {}
    for k = 0x10, 0x1c, 4 do st[#st + 1] = string.format("%x", mem[sp + k] + mem[sp + k + 1] * 256) end
    L.log(string.format("txt %d ra=%08x a0=%x a1=%x a2=%x a3=%x stack=%s %s", L.frame, r.ra % 0x100000000,
      r.a0 % 0x100000000, r.a1 % 0x100000000, r.a2 % 0x100000000, r.a3 % 0x100000000, table.concat(st, ","),
      table.concat(strs, " ")))
  end
end)
