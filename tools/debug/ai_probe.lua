-- Probe for the battle talk path (docs/re/scenes.md §BSX battle talk): logs every record the AI interpreter
-- (0x8003c8f4) runs, every entry into the talk sub-interpreter (0x8003c4a0) with its stream bytes and the table index
-- gp+0xcb0, and the AI talk op handlers (op 0 0x8003c950, op 3 0x8003ca74, op 4 0x8003cae4) that gate a line.
-- Use it to find out why a talk line does or does not appear, and which record the handler hands over:
--   emu.py build/kuro_en.cue --state-in work/states/base_kuro_en.sstate --script tools/debug/warp.lua
--     --script tools/debug/ai_probe.lua --var "SCENE='battle_talk_ko'" --var "KEEP=1" --debugger --frames 3000
-- Result 2026-11-02 (scene battle_talk_ko): the AI runs the op-04 record at frame 1379, the handler is entered, and
-- the talk interpreter gets `04 02 74 08 6a 08` with gp+0xcb0 = 0 (entry 0 = 0x874).
local mem = PCSX.getMemPtr()
local function u8(a) return mem[a % 0x200000] end
local function u32(a) return u8(a) + u8(a + 1) * 256 + u8(a + 2) * 65536 + u8(a + 3) * 16777216 end
local function log_rec(tag)
  return function()
    local r = PCSX.getRegisters().GPR.n
    local a = tag == "AI" and (r.a1 or 0) or (r.a0 or 0)
    L.log(string.format("%s frame %d stream %08x bytes %02x %02x %02x %02x cb0 %d", tag, L.frame, a,
      u8(a), u8(a + 1), u8(a + 2), u8(a + 3), u32(0x88f8c)))
  end
end
L.on_exec(0x8003c8f4, log_rec("AI"))
L.on_exec(0x8003c4a0, log_rec("talk"))
L.on_exec(0x8003c950, function() L.log(string.format("op0 handler frame %d", L.frame)) end)
L.on_exec(0x8003ca74, function() L.log(string.format("op3 handler frame %d", L.frame)) end)
L.on_exec(0x8003cae4, function() L.log(string.format("op4 handler frame %d", L.frame)) end)
L.on_frame(function(n)
  if n % 400 == 0 then   -- actor table + the two gate bytes, so a held value can be checked against the run
    local p = u32(0x94dd8)
    L.log(string.format("%d actor0 %08x hp@14 %d f0d %d 5e %d b8 %d", n, p, u32(p + 0x14) % 65536,
      u8(0x88f0d), u8(0x8905e), u8(0x890b8)))
  end
end)
