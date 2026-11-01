"""re.py: recon helpers for SLPS_010.30 (PS-X EXE, MIPS R3000).

    python -X utf8 tools/re.py imm EXE VALUE        # instructions loading VALUE as an immediate (li/addiu/ori/slti*)
    python -X utf8 tools/re.py dis EXE ADDR [N]     # disassemble N instructions at RAM ADDR
    python -X utf8 tools/re.py jt EXE MIN_ENTRIES   # word tables of code pointers (switch/dispatch tables)
"""
import struct
import sys
from pathlib import Path

import capstone


def load(path):
    b = Path(path).read_bytes()
    assert b[:8] == b"PS-X EXE"
    t_addr, t_size = struct.unpack_from("<II", b, 0x18)
    return t_addr, b[0x800:0x800 + t_size]


def dis(base, code, addr, n=40):
    md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
    off = addr - base
    for ins in md.disasm(code[off:off + 4 * n], addr):
        print(f"{ins.address:08x}  {ins.mnemonic:8s} {ins.op_str}")


def imm(base, code, value):
    for off in range(0, len(code) - 3, 4):
        w = struct.unpack_from("<I", code, off)[0]
        op = w >> 26
        if op in (0x08, 0x09, 0x0a, 0x0b, 0x0d) and (w & 0xFFFF) == value:   # addi addiu slti sltiu ori
            yield base + off, w


def jumptables(base, code, minimum):
    end = base + len(code)
    run = []
    for off in range(0, len(code) - 3, 4):
        w = struct.unpack_from("<I", code, off)[0]
        if base <= w < end and w % 4 == 0:
            run.append(w)
            continue
        if len(run) >= minimum:
            yield base + off - 4 * len(run), run
        run = []


if __name__ == "__main__":
    cmd, exe = sys.argv[1], sys.argv[2]
    base, code = load(exe)
    if cmd == "dis":
        dis(base, code, int(sys.argv[3], 16), int(sys.argv[4]) if len(sys.argv) > 4 else 40)
    elif cmd == "imm":
        for a, w in imm(base, code, int(sys.argv[3], 0)):
            print(f"{a:08x} {w:08x}")
    elif cmd == "jt":
        for a, run in jumptables(base, code, int(sys.argv[3])):
            print(f"{a:08x} {len(run):4d} {run[0]:08x}..")
