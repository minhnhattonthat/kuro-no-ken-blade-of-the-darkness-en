-- Log every CD-ROM Setloc target (LBA) the game issues, one line per seek: "f<frame> setloc <lba> pc=<pc>".
--   emu.py CUE ... --debugger --script tools/debug/cd_seeks.lua
-- Hooks writes to the CD param (0x1F801802) and command (0x1F801801) ports and reads the stored byte from the
-- store instruction's source register. Used for the phase 3 LBA-shift test (docs/re/archives.md).
local ffi = require("ffi")
local params = {}
local function stored_byte()
  local pc = L.pc()
  local mem = ffi.cast("uint32_t*", PCSX.getMemPtr())
  local ins = mem[bit.rshift(bit.band(pc, 0x1fffff), 2)]
  local rt = bit.band(bit.rshift(ins, 16), 31)
  return bit.band(PCSX.getRegisters().GPR.r[rt], 0xff), pc
end
local function bcd(b) return bit.rshift(b, 4) * 10 + bit.band(b, 15) end
L.on_write(0x1F801802, 0x1F801802, function()
  params[#params + 1] = stored_byte()
end)
L.on_write(0x1F801801, 0x1F801801, function()
  local cmd, pc = stored_byte()
  -- index register (0x1F801800) is 0 for command writes; Setloc = 0x02 with 3 BCD params mm ss ff
  if cmd == 0x02 and #params >= 3 then
    local n = #params
    local lba = (bcd(params[n - 2]) * 60 + bcd(params[n - 1])) * 75 + bcd(params[n]) - 150
    L.log(string.format("f%d setloc %d pc=%08X", L.frame, lba, pc))
  end
  params = {}
end)
