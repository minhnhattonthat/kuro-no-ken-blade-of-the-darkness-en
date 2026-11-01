"""texttest.py: show a string in a real field message box (the 02OLB01 inn greeting), from a cold warp.

    python -X utf8 tools/debug/texttest.py "TEXT" [--out work/qa/texttest] [--frames 1400] [--at 0x38e5]

The message op at 0x38e3 (3b 02 <38 bytes> 00) belongs to the item shop/inn script; the inn scene triggers it.
Used for font sheets and the width gate before the marker build exists (AGENTS.md: warp, not play).
"""
import argparse
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

SLOT = 38   # bytes of the original message text, escapes included


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("text")
    ap.add_argument("--out", default="work/qa/texttest")
    ap.add_argument("--frames", default="1600")
    ap.add_argument("--at", default="0x38e5", help="script address of the message text")
    ap.add_argument("--scene", default="inn")
    ap.add_argument("--state", default="work/states/base_kuro_en.sstate",
                    help="base state made on THIS build (a state from another build keeps that build's EXE and font)")
    a = ap.parse_args()
    raw = a.text.encode("cp932", "replace")
    assert len(raw) <= SLOT, f"{len(raw)} bytes > {SLOT}: shorten the text or use escapes"
    raw = raw + b"\0" * (SLOT - len(raw))
    patch = f"02olb01:{int(a.at, 0):04x}:{raw.hex()}"
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), "build/kuro_en.cue",
           "--out", a.out, "--state-in", a.state,
           "--script", "tools/debug/warp.lua", "--var", f"SCENE='{a.scene}'", "--var", f"PATCH='{patch}'",
           "--frames", a.frames, "--shot-every", "100"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    print(r.stdout.strip().splitlines()[-1] if r.stdout.strip() else r.stderr[-800:])
    log = Path(a.out, "log.txt")
    if log.exists():
        for line in log.read_text(encoding="utf-8", errors="replace").splitlines():
            if "patch" in line or "proof" in line:
                print(line)


if __name__ == "__main__":
    main()
