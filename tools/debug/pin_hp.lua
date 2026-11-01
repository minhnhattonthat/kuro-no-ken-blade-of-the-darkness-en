-- Fight helper. Actor records: pointer table at 0x80094dd8 (6 x u32: party 0x800945f0, 0x8009470c, 0x80094828,
-- then enemies 0x80094944, ...); per record u32 HP cur at +0x14, max at +0x18 (party MP +0x1c/+0x20).
-- PIN (default 1): every frame, the two party records' HP cur = max (keeps the party alive).
-- HP_AT = "addr" (u32, e.g. 0x80094604 = Kaies' HP cur) + HP = value: from SET_AT frames on, write it once
-- (cross a BSX talk trigger such as AI op 4 "actor 0 HP == 0", docs/re/scenes.md §BSX talk refs).
local mem = PCSX.getMemPtr()
local function rd32(a) a = a % 0x200000; return mem[a] + mem[a + 1] * 256 + mem[a + 2] * 65536 + mem[a + 3] * 16777216 end
local function wr32(a, v) a = a % 0x200000; for i = 0, 3 do mem[a + i] = math.floor(v / 256 ^ i) % 256 end end
local PARTY = { 0x80094604, 0x80094720 }
local done = false
L.on_frame(function(n)
  if (PIN or 1) ~= 0 then
    for _, p in ipairs((PIN or 1) > 1 and { PIN } or PARTY) do   -- PIN = an HP address pins only that record
      local mx = rd32(p + 4)
      if mx > 0 and mx < 100000 and rd32(p) < mx then wr32(p, mx) end
    end
  end
  if HP_AT and not done and n >= (SET_AT or 0) then
    wr32(HP_AT, HP or 1); done = true
    L.log(string.format("%d hp %08x -> %d", n, HP_AT, HP or 1))
  end
  -- BYTE_AT + BYTE: hold one byte from SET_AT on, e.g. BYTE_AT=0x80088f4a (gp+0xc6e) BYTE=1 fires AI op 3's talk
  if BYTE_AT and n >= (SET_AT or 0) and mem[BYTE_AT % 0x200000] ~= (BYTE or 1) then
    mem[BYTE_AT % 0x200000] = BYTE or 1
    L.log(string.format("%d byte %08x -> %d", n, BYTE_AT, BYTE or 1))
  end
end)
