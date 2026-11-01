-- Recon: log every file lookup (0x80012d50(length, name)) with the frame, so a build that hangs on
-- "Now Loading" shows which file it keeps asking for. Needs emu.py --debugger.
local mem = PCSX.getMemPtr()
local seen = {}
L.on_exec(0x80012d50, function()
  local r = PCSX.getRegisters().GPR.n
  local p = r.a1
  local t = {}
  for i = 0, 15 do
    local c = mem[(p + i) % 0x200000]
    if c == 0 then break end
    t[#t + 1] = string.char(c)
  end
  local name = table.concat(t)
  local key = name .. "@" .. tostring(math.floor(L.frame / 60))
  if seen[key] then return end
  seen[key] = true
  if L.frame <= (UNTIL or 1e9) then L.log(string.format("open f%d %q (%d)", L.frame, name, r.a0)) end
end)
