-- Recon probe: which code draws VIS/MES captions? Logs each distinct caller (ra) of the BIOS kanji font call
-- Krom2RawAdd (0x80067f38), of the caption parser 0x8005fd3c and of its glyph step 0x8005f684 (docs/re/font.md).
-- Use with warp.lua and --debugger.
local seen = {}
local function hook(addr, name)
  L.on_exec(addr, function()
    local r = PCSX.getRegisters().GPR.n
    local key = name .. string.format("%08x", r.ra % 0x100000000)
    if not seen[key] then
      seen[key] = true
      L.log(string.format("krom %d %s ra=%08x a0=%x a1=%x a2=%x", L.frame, name, r.ra % 0x100000000,
        r.a0 % 0x100000000, r.a1 % 0x100000000, r.a2 % 0x100000000))
    end
  end)
end
hook(0x80067f38, "krom")
hook(0x8005fd3c, "parser")
hook(0x8005f684, "glyph")
