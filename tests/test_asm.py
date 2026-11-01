"""Phase 5: EXE hooks (tools/asm/*.asm), run under unicorn with exact-PC checks."""
import shutil
import struct
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import fnt      # noqa: E402

EXE = ROOT / "work" / "orig" / "tree" / "SLPS_010.30"
FNT = ROOT / "work" / "orig" / "mps" / "SYS" / "SYSTEM.FNT"
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"
unicorn = pytest.importorskip("unicorn")
need = pytest.mark.skipif(not (EXE.is_file() and FNT.is_file() and ARMIPS.is_file()), reason="no dump/armips")

GP, HALF, RET = 0x800882DC, 0x80150010, 0x80001000
ASCII_GLYPH, BUF = 0x80060054, 0x80156800


def patched(tmp_path):
    exe = tmp_path / "SLPS_010.30"
    shutil.copy(EXE, exe)
    subprocess.run([str(ARMIPS), str(ROOT / "tools" / "asm" / "vis_ascii.asm"), "-strequ", "EXE", str(exe),
                    "-erroronwarning"], check=True, capture_output=True)
    return exe.read_bytes()


def uc(exe):
    """Unicorn with PS1 main RAM. Unicorn fetches kseg0 (0x8xxxxxxx) from physical memory, so RAM is mapped at 0
    and written/read at `a & 0x1fffffff`."""
    from unicorn import Uc, UC_ARCH_MIPS, UC_MODE_MIPS32, UC_MODE_LITTLE_ENDIAN
    mu = Uc(UC_ARCH_MIPS, UC_MODE_MIPS32 + UC_MODE_LITTLE_ENDIAN)
    mu.mem_map(0, 0x200000)
    mu.mem_write(0x10000, exe[0x800:])
    return mu


def P(a):
    return a & 0x1FFFFFFF


def run_glyph(exe, code):
    from unicorn import mips_const as m
    mu = uc(exe)
    mu.mem_write(P(HALF), FNT.read_bytes()[0x10:0x2410])
    mu.mem_write(P(GP + 0xE04), struct.pack("<I", HALF))
    mu.mem_write(P(BUF), b"\xaa" * 64)                     # stale bytes the converter must clear
    mu.reg_write(m.UC_MIPS_REG_GP, GP)
    mu.reg_write(m.UC_MIPS_REG_A0, code)
    mu.reg_write(m.UC_MIPS_REG_RA, RET)
    mu.reg_write(m.UC_MIPS_REG_SP, 0x801F0000)
    mu.emu_start(ASCII_GLYPH, RET, count=5000)
    assert mu.reg_read(m.UC_MIPS_REG_PC) == RET            # returned, not ran off
    assert mu.reg_read(m.UC_MIPS_REG_V0) == BUF
    return bytes(mu.mem_read(P(BUF), 64))


@need
def test_vis_ascii_glyph_matches_half_width_font(tmp_path):
    exe = patched(tmp_path)
    data = FNT.read_bytes()
    for code in (0x41, 0x67, 0x2E, 0x20):
        got = run_glyph(exe, code)
        want = bytearray(32)
        for y, row in enumerate(fnt.ascii_rows(data, code)):
            want[2 * (2 + y)] = sum(1 << (7 - x) for x, v in enumerate(row) if v)
        assert got[:32] == bytes(want), hex(code)
        assert got[32:] == b"\xaa" * 32                    # nothing written past the 32-byte cell
    assert any(run_glyph(exe, 0x41)[:30])


@need
def test_vis_ascii_sjis_still_goes_to_bios(tmp_path):
    """A code >= 0x80 must tail-jump to Krom2RawAdd (0x80067f38) with a0 untouched."""
    from unicorn import mips_const as m
    mu = uc(patched(tmp_path))
    mu.reg_write(m.UC_MIPS_REG_A0, 0x8260)
    mu.reg_write(m.UC_MIPS_REG_RA, RET)
    mu.emu_start(ASCII_GLYPH, 0x80067F38, count=50)
    assert mu.reg_read(m.UC_MIPS_REG_PC) == 0x80067F38
    assert mu.reg_read(m.UC_MIPS_REG_A0) == 0x8260
