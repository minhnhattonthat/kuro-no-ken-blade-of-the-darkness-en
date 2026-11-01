"""build.py: build/kuro_en.cue + .bin from the pinned dump.

    python -X utf8 tools/build.py

Steps: check the dump against rom.sha1, unpack it once into work/orig/tree (dumpsxiso), copy that tree to
work/build/tree, apply the edits, repack with mkpsxiso using the dump's own layout.xml. Files are found by name
(CdSearchFile), so files may grow and shift LBAs (docs/re/archives.md, phase 3 LBA-shift test)."""
import hashlib
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_rom  # noqa: E402

ORIG = ROOT / "work" / "orig"
WORK = ROOT / "work" / "build"
OUT = ROOT / "build" / "kuro_en.bin"
MKPSXISO = ROOT / "tools" / "mkpsxiso" / "mkpsxiso.exe"
DUMPSXISO = ROOT / "tools" / "mkpsxiso" / "dumpsxiso.exe"


def unpack():
    """work/orig/tree + layout.xml from the dump (once)."""
    if (ORIG / "tree" / "SLPS_010.30").is_file() and (ORIG / "layout.xml").is_file():
        return
    subprocess.run([sys.executable, str(ROOT / "tools" / "orig_cue.py")], check=True)
    subprocess.run([str(DUMPSXISO), "-x", "tree", "-s", "layout.xml", "kuro.cue"], cwd=ORIG, check=True)


def repack(base, out):
    """mkpsxiso on base/tree with the dump's layout (its paths are 'tree/...', so the layout sits in base)."""
    base, out = Path(base), Path(out)
    if base != ORIG:
        shutil.copyfile(ORIG / "layout.xml", base / "layout.xml")
    out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([str(MKPSXISO), "-q", "-y", "-o", str(out), "-c", str(out.with_suffix(".cue")), "layout.xml"],
                   cwd=base, check=True)
    return out


def sha1(path):
    with open(path, "rb") as f:
        return hashlib.file_digest(f, "sha1").hexdigest()


def edit(tree):
    """Apply every edit to the copied tree. None yet (phase 4+: script, font, graphics, EXE)."""


def main():
    check_rom.check()
    unpack()
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(ORIG / "tree", WORK / "tree")
    edit(WORK / "tree")
    repack(WORK, OUT)
    print(f"{OUT.relative_to(ROOT)}  sha1 {sha1(OUT)}")


if __name__ == "__main__":
    main()
