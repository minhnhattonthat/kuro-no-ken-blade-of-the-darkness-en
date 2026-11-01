-- Recon probe (needs emu.py --debugger): log every script op the interpreter fetches, as
-- "frame scriptaddr op" (script address = RAM - 0x80168000; slots 0x0000 area, 0x2000 map, 0x4000 99CMN,
-- 0x5000 event). Fetch site: 0x8002c924 lbu $v0,($v0) in the main loop at 0x8002c8c0. Ops 0xff fetch a sub-op in
-- the extended interpreter, logged separately as "x". TRACE_FROM/TRACE_TO limit the frame window.
local mem = PCSX.getMemPtr()
local lo, hi = TRACE_FROM or 0, TRACE_TO or 1e9
L.on_exec(0x8002c924, function()
  if L.frame < lo or L.frame > hi then return end
  local p = PCSX.getRegisters().GPR.n.v0
  local a = (p - 0x80168000) % 0x100000000
  L.log(string.format("%d %04x %02x", L.frame, a, mem[p % 0x200000]))
end)
