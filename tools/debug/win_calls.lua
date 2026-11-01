-- Recon probe: log every call of the window/menu creators with its arguments and caller (emu.py --debugger).
--   0x80053744(id, &menu, w, h)   menus (w/h in 8 px units)
--   0x80054448(id, &win, ...)     windows (0x800544b8 wraps it)
-- Output: "win <frame> <fn> ra=<caller> a0..a3 [16 bytes at a1]"
local mem = PCSX.getMemPtr()
local function hook(addr, name)
  L.on_exec(addr, function()
    local r = PCSX.getRegisters().GPR.n
    local out = {}
    for i = 0, 15 do out[#out + 1] = string.format("%02x", mem[(r.a1 + i) % 0x200000]) end
    L.log(string.format("win %d %s ra=%08x a0=%x a1=%08x a2=%x a3=%x [%s]", L.frame, name, r.ra % 0x100000000,
      r.a0 % 0x100000000, r.a1 % 0x100000000, r.a2 % 0x100000000, r.a3 % 0x100000000, table.concat(out, " ")))
  end)
end
hook(0x80053744, "menu")
hook(0x80054448, "window")
