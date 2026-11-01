-- QA probe: force every battle ailment marker on (member flags +0x5e bits 1/2/4/8: poison, silence-or-seal,
-- paralysis, sleep) just before the status box reads them (0x8005c60c, s2 = member), so the ST row shows all four.
-- Use with warp.lua and --debugger: emu.py ... --script tools/debug/warp.lua --script tools/debug/ailments.lua
local mem = PCSX.getMemPtr()
L.on_exec(0x8005c60c, function()
  local s2 = PCSX.getRegisters().GPR.n.s2 % 0x200000
  mem[s2 + 0x5e] = bit.bor(mem[s2 + 0x5e], AILMENTS or 0x0f)
end)
