-- Recon probe: dump main RAM (ram_<frame>.bin in --out) at the frames listed in DUMPS, e.g. --var "DUMPS={30,90}".
local want = {}
for _, f in ipairs(DUMPS or {}) do want[f] = true end
L.on_frame(function(n)
  if want[n] then L.dump_ram(string.format("ram_%06d.bin", n)); L.shot(string.format("d%06d.png", n)) end
end)
