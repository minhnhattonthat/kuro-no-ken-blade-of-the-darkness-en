-- Recon probe: which bytes of a RAM block does the game actually read? Logs every CPU read inside SLOT..SLOT+SIZE-1
-- as "frame offset pc" (aggregated), then reports the byte ranges never read, so a data block can be shown to be
-- unused (or which parts of it the engine uses). Used for the "BSX action labels are never read" proof: in a whole
-- fight 172 of the 721 loaded bytes were read, and the label runs were not among them (docs/re/scenes.md).
--
-- Run with warp.lua (breakpoints need the interpreter: --debugger):
--   emu.py build/kuro_en.cue --state-in work/states/base_kuro_en.sstate --script tools/debug/warp.lua
--     --script tools/debug/slot_reads.lua --var "SCENE='battle_boss'" --var "KEEP=1" --debugger --frames 2600
-- Vars: SLOT/SIZE = the block (default the loaded BSX file: 0x80099170, 0x1400); LEN = the block's real length in
-- bytes for the "never read" report (default SIZE); the summary goes to OUT/slot_reads.txt.
local SLOT = SLOT or 0x80099170
local SIZE = SIZE or 0x1400
local LEN = LEN or SIZE
local reads, total, touched = {}, 0, {}
local function note(addr)
  total = total + 1
  local off = addr - SLOT
  touched[off] = true
  local k = string.format("%5d %04x %08x", L.frame, off, L.pc() % 0x100000000)
  reads[k] = (reads[k] or 0) + 1
end
for i = 0, math.ceil(SIZE / 0x100) - 1 do
  local lo, hi = SLOT + i * 0x100, math.min(SLOT + (i + 1) * 0x100 - 1, SLOT + SIZE - 1)
  L.on_read(lo, hi, function(addr) note(addr) end)
end
local function ranges(list)   -- coalesce a sorted offset list into "start-end" spans
  local out, s, last = {}, nil, nil
  for _, off in ipairs(list) do
    if s == nil then s, last = off, off
    elseif off == last + 1 then last = off
    else out[#out + 1] = s == last and string.format("%04x", s) or string.format("%04x-%04x", s, last); s, last = off, off end
  end
  if s then out[#out + 1] = s == last and string.format("%04x", s) or string.format("%04x-%04x", s, last) end
  return out
end
L.on_frame(function(n)
  if n % 400 == 0 then L.log(string.format("frame %d: %d reads", n, total)) end
  if FRAMES and n == FRAMES - 1 then
    local used, unused = {}, {}
    for off = 0, LEN - 1 do
      if touched[off] then used[#used + 1] = off else unused[#unused + 1] = off end
    end
    local keys = {}
    for k in pairs(reads) do keys[#keys + 1] = k end
    table.sort(keys)
    local ur, uu = ranges(used), ranges(unused)
    local out = { string.format("reads %d, distinct offsets %d of %d bytes; never read: %d bytes", total,
      #used, LEN, #unused) }
    if #uu > 0 then out[#out + 1] = "never read: " .. table.concat(uu, " ") end
    for _, k in ipairs(keys) do out[#out + 1] = k .. " x" .. reads[k] end
    L.write_file("slot_reads.txt", table.concat(out, "\n") .. "\n")
    L.log(out[1] .. (#uu > 0 and ("; never read: " .. table.concat(uu, " ")) or ""))
  end
end)
