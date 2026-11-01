-- Recon: count calls of the text layout / glyph draw functions per frame window.
--   TEXT_LAYOUT (default 0x80051904)  window text layout
--   GLYPH_FN    (default 0x80050508)  per-character sprite
local layout, glyph = TEXT_LAYOUT or 0x80051904, GLYPH_FN or 0x80050508
local nl, ng = 0, 0
L.on_exec(layout, function() nl = nl + 1 end)
L.on_exec(glyph, function()
  ng = ng + 1
  if ng <= (SHOW or 10) then
    local r = PCSX.getRegisters().GPR.n
    L.log(string.format("glyph f%d code=%04x a3=%04x", L.frame, r.a0 % 0x10000, r.a3 % 0x10000))
  end
end)
L.on_frame(function(n)
  if n % 600 == 0 then L.log(string.format("counts f%d layout=%d glyph=%d", n, nl, ng)) end
end)
