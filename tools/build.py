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
ARMIPS = ROOT / "tools" / "armips" / "armips.exe"


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
    """Apply every edit to the copied tree: the English of script/**/*.json (tools/insert.py).
    `--marker` replaces every string with its [id] marker instead (the phase-5 marker build)."""
    import insert
    marker = "--marker" in sys.argv
    if "--data-runs" in sys.argv:               # also write SCN data runs (choices), in place (insert.DATA_RUNS)
        insert.DATA_RUNS = 1
    insert.GROW = "--no-grow" not in sys.argv   # bisecting: keep every SCN file at its own size
    for i, a in enumerate(sys.argv):            # --qa ID=TEXT: stress one line (width gate)
        if a == "--only":                       # bisecting: only these SCN files (comma list, "" = none) get English
            insert.ONLY = set(filter(None, sys.argv[i + 1].upper().split(",")))
        if a == "--skip":
            insert.SKIP = set(sys.argv[i + 1].split(","))
        if a == "--legacy":
            insert.LEGACY = set(sys.argv[i + 1].split(","))
        if a == "--out":                      # another output .bin (parallel experiments)
            global OUT
            OUT = ROOT / sys.argv[i + 1]
        if a == "--qa":
            k, v = sys.argv[i + 1].split("=", 1)
            insert.QA[k] = v
    notes, written, moved = insert.apply(tree, marker=marker)
    print(f"insert: {written} strings, {moved} message ops relocated"
          + (f", {len(notes)} sites too small for the marker" if marker else f", {len(notes)} problems"))
    for n in notes[:10]:
        print("  -", n)
    if not marker and notes and "--keep-going" not in sys.argv:     # --keep-going: build anyway (iteration)
        raise SystemExit("insert: English that does not fit its site (see above)")
    import fnt
    import mps
    sys_mps = tree / "SYS.MPS"
    start, ents = mps.read(sys_mps.read_bytes())
    ents = [(n, fnt.patch_ascii(b)[0] if n == "SYSTEM.FNT" else b) for n, _o, b in ents]
    sys_mps.write_bytes(mps.write(ents, start))
    print("font: ASCII punctuation glyphs written")
    for src in sorted((ROOT / "tools" / "asm").glob("*.asm")):   # EXE hooks (docs/re/font.md)
        subprocess.run([str(ARMIPS), str(src), "-strequ", "EXE", str(tree / "SLPS_010.30"), "-erroronwarning"],
                       check=True)
        print(f"asm: {src.name}")
    ranges = [ln.split("#")[0].strip() for ln in open(ROOT / "data" / "exe_allowed.txt", encoding="utf-8")]
    ranges = [r for r in ranges if r] + [f"{w:x}-{w + 3:x}" for w in insert.EXE_WRITES]
    subprocess.run([sys.executable, str(ROOT / "tools" / "romdiff.py"), str(ORIG / "tree" / "SLPS_010.30"),
                    str(tree / "SLPS_010.30")] + ranges, check=True)   # nothing written outside them


def main():
    check_rom.check()
    unpack()
    if WORK.exists():
        shutil.rmtree(WORK)
    shutil.copytree(ORIG / "tree", WORK / "tree")
    edit(WORK / "tree")
    out = OUT.with_name("kuro_marker.bin") if "--marker" in sys.argv else OUT
    repack(WORK, out)
    print(f"{out.relative_to(ROOT)}  sha1 {sha1(out)}")


if __name__ == "__main__":
    main()
