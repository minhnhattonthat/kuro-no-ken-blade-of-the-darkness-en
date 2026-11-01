-- QA probe: when a battle's BSX lands in its slot at 0x80099170 (the loader copies the whole file there), overwrite
-- it with BSX_FILE (a BSX taken from a build, e.g. one with battle talk), so any reachable fight (battle_fight)
-- runs that battle's script and shows its talk. Polls once a frame (an exec breakpoint needs --debugger, which runs
-- ~10x slower): a new file shows as a changed first 16 bytes. BSX_FILE must be an absolute path.
--   emu.py ... --script tools/debug/warp.lua --script tools/debug/bsx_swap.lua --var "BSX_FILE='H:/.../X.BSX'"
local mem = PCSX.getMemPtr()
local f = assert(io.open(BSX_FILE, "rb"))
local data = f:read("*a")
f:close()
local function head()
  local t = {}
  for i = 0, 15 do t[#t + 1] = string.char(mem[0x99170 + i]) end
  return table.concat(t)
end
local mine, last = data:sub(1, 16), nil
L.on_frame(function(n)
  -- a BSX starts 00 00 00 00 .. .. 3c 00 (other data uses this RAM outside battle)
  if mem[0x99176] ~= 0x3c or mem[0x99177] ~= 0 or mem[0x99170] + mem[0x99171] + mem[0x99172] + mem[0x99173] ~= 0 then
    return
  end
  local h = head()
  if h ~= last and h ~= mine then
    for i = 1, #data do mem[0x99170 + i - 1] = data:byte(i) end
    L.log(string.format("%d bsx_swap: %d bytes from %s", n or -1, #data, BSX_FILE))
    h = mine
  end
  last = h
end)
