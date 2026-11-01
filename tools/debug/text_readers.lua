-- Recon: which code reads the MES text buffer? Set READ_LO/READ_HI (default the VIS02 page text) and this logs
-- one line per distinct PC that reads inside the range, with the frame. Needs emu.py --debugger.
local lo, hi = READ_LO or 0x80158060, READ_HI or 0x801580a0
local seen, n = {}, 0
local mem = PCSX.getMemPtr()
L.on_read(lo, hi, function(addr)
  local pc = L.pc()
  if seen[pc] then return end
  seen[pc] = true
  n = n + 1
  if n <= (SHOW or 40) then
    local r = PCSX.getRegisters().GPR.n
    L.log(string.format("read f%d pc=%08x addr=%08x ra=%08x a0=%08x a1=%08x v0=%08x",
      L.frame, pc, addr, r.ra, r.a0, r.a1, r.v0))
  end
end)
L.on_frame(function(f) if f % 300 == 0 then L.log(string.format("reads f%d distinct=%d", f, n)) end end)
