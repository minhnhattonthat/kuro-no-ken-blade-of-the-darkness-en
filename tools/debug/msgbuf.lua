-- Probe: high-water mark of the field message buffer (0x80090348, 512 bytes up to 0x80090548). Op 3b appends
-- its string at the pointer in 0x80088c9c; ops 37/38/39 show the buffer and reset the pointer. Logs every new
-- maximum with the script address and the slot names, and "OVERFLOW" once the pointer passes the end.
-- Run beside warp.lua: --script tools/debug/warp.lua --script tools/debug/msgbuf.lua
local mem = PCSX.getMemPtr()
local function u32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local function cstr(a)
  local t = {}
  for i = 0, 15 do local c = mem[(a + i) % 0x200000]; if c == 0 then break end; t[#t + 1] = string.char(c) end
  return table.concat(t)
end
local top = 0
L.on_frame(function(n)
  local used = u32(0x80088c9c) - 0x80090348
  if TRACE_FROM and n >= TRACE_FROM and n % 50 == 0 then    -- --var TRACE_FROM=16000: script pointer trace
    L.log(string.format("%d scr=%05x buf=%08x %s|%s|%s", n, (u32(0x80088fd4) - 0x80168000) % 0x100000,
      u32(0x80088c9c), cstr(0x800ce2a8), cstr(0x800ce2b8), cstr(0x800ce2c8)))
  end
  if used > top and used < 0x10000 then
    top = used
    local scr = (u32(0x80088fd4) - 0x80168000) % 0x10000
    L.log(string.format("%d msgbuf %d bytes%s scr=%04x %s|%s|%s", n, used, used > 512 and " OVERFLOW" or "",
      scr, cstr(0x800ce2a8), cstr(0x800ce2b8), cstr(0x800ce2c8)))
  end
end)
