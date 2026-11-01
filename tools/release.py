"""release.py: tests + lint -> build -> boot smoke -> leftover Japanese -> screen tour -> QA gates (visual + story)
-> polish list -> xdelta3 patch -> re-apply and compare -> README + zip. Stops at the first failure.

    python -X utf8 tools/release.py VERSION [--force] [--no-tour]     (e.g. 1.0) -> release/KuroNoKen_EN_vVERSION.zip

The patch is against the .bin in rom/ (rom.sha1); the zip holds the patch and README.txt only (no .cue: players keep
their own). The tour re-shoots every scene into work/qa/v8/scenes and re-hashes the visual-QA manifest, so a sheet
whose pixels changed needs a new verdict before the gate passes; --no-tour reuses the last shots (iteration only).
Release dirs stay local (gitignored); publishing is the user's call. The playable image stays in build/. The debug
tool (tools/debug/*.lua) runs only inside the emulator and is never part of the image.
"""
import argparse
import hashlib
import shutil
import subprocess
import sys
import zipfile
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from skill import SKILL  # noqa: E402

SCRIPTS = Path(SKILL) / "scripts"
ROM = ROOT / "rom/Kuro no Ken - Blade of the Darkness (Japan).bin"
BUILT = ROOT / "build/kuro_en.bin"
QA = ROOT / "work/qa"
PY = (sys.executable, "-X", "utf8")


def run(*cmd, **kw):
    p = subprocess.run([str(c) for c in cmd], cwd=ROOT, **kw)
    if p.returncode:
        sys.exit(f"failed: {' '.join(map(str, cmd))}")
    return p


def hashes(p):
    md5, sha1, crc = hashlib.md5(), hashlib.sha1(), 0
    with open(p, "rb") as f:
        while b := f.read(1 << 22):
            crc = zlib.crc32(b, crc)
            md5.update(b)
            sha1.update(b)
    return {"size": p.stat().st_size, "crc32": f"{crc:08x}", "md5": md5.hexdigest(), "sha1": sha1.hexdigest()}


def leftover():
    """Japanese left unchanged in the EXE text areas (jp_left.py --orig; extract.EXE_RANGES). Archive text (SCN, MES,
    SMX, BSX talk) is covered by check.py: lint fails a Japanese unit with no English and extract check fails on
    text outside the extracted entries. The old JP choice tables stay in SCN files, unreferenced (op 7d points at
    the English copy)."""
    import extract
    ranges = [a for lo, hi in extract.EXE_RANGES for a in ("--range", f"{lo:x}-{hi:x}")]
    p = subprocess.run([*PY, str(SCRIPTS / "jp_left.py"), "work/build/tree/SLPS_010.30", "--orig",
                        "work/orig/tree/SLPS_010.30", "--sjis", *ranges], cwd=ROOT, capture_output=True, text=True,
                       encoding="utf-8")
    return "" if p.stdout.rstrip().endswith("0 Japanese runs, 0 bytes (unchanged from original)") else p.stdout + p.stderr


def tour():
    """Every scene re-shot on this build; the proofs replace work/qa/v8/scenes (prologue_* come from the FMV run and
    are kept), then the manifest is re-hashed."""
    out = QA / "tour_release"
    shutil.rmtree(out, ignore_errors=True)
    run(*PY, "tools/debug/tour.py", "--cue", BUILT.with_suffix(".cue"), "--jobs", "4", "--out", out)
    for png in out.glob("*.png"):
        if not png.name.startswith("sheet"):
            shutil.copy(png, QA / "v8/scenes" / png.name)
    run(*PY, SCRIPTS / "qa_gate.py", "init", QA / "v8/manifest.tsv", QA / "v8/scenes", "--glob", "*.png")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("version")
    ap.add_argument("--force", action="store_true", help="overwrite this version's existing release files")
    ap.add_argument("--no-tour", action="store_true", help="reuse the last tour shots (iteration only)")
    a = ap.parse_args()
    name = f"KuroNoKen_EN_v{a.version}"
    rel, z = ROOT / "release" / f"v{a.version}", ROOT / "release" / f"{name}.zip"
    if (rel.exists() or z.exists()) and not a.force:
        sys.exit(f"{rel} exists; pass --force to overwrite")

    run(*PY, "tools/check.py")
    run(*PY, "tools/batches.py", "lint")
    run(*PY, "tools/extract.py", "check")
    run(*PY, "tools/build.py")
    run(*PY, SCRIPTS / "emu.py", BUILT.with_suffix(".cue"), "--out", QA / "release_smoke",
        "--route", "tools/routes/boot.txt", "--smoke")
    if bad := leftover():
        sys.exit("Japanese left in the EXE:\n" + bad)
    if not a.no_tour:
        tour()
    run(*PY, SCRIPTS / "qa_gate.py", "check", QA / "v8/manifest.tsv", QA / "v8/verdicts")
    run(*PY, SCRIPTS / "qa_gate.py", "check", QA / "story/manifest.tsv", QA / "story/verdicts")
    if open_ := [s for s in (ROOT / "docs/polish.md").read_text(encoding="utf-8").splitlines()
                 if s.lstrip().startswith("- [ ]")]:
        sys.exit("unticked docs/polish.md lines:\n" + "\n".join(open_))

    shutil.rmtree(rel, ignore_errors=True)
    rel.mkdir(parents=True)
    patch = rel / f"{name}.xdelta"
    run("xdelta3", "-e", "-9", "-f", "-s", ROM, BUILT, patch)
    test = ROOT / "work/release_reapplied.bin"
    run("xdelta3", "-d", "-f", "-s", ROM, patch, test)
    o, b = hashes(ROM), hashes(BUILT)
    if hashes(test)["sha1"] != b["sha1"]:
        sys.exit("re-applied patch differs from the build")
    test.unlink()
    info = (f"{ROM.name}\n  size {o['size']}  CRC32 {o['crc32']}\n  MD5 {o['md5']}\n  SHA-1 {o['sha1']}\n"
            f"  Redump: http://redump.org/discs/quicksearch/{o['sha1']}\n"
            f"Patched .bin: size {b['size']}  CRC32 {b['crc32']}  SHA-1 {b['sha1']}")
    readme = (ROOT / "docs/README.template.txt").read_text(encoding="utf-8")
    (rel / "README.txt").write_text(readme.replace("{VERSION}", a.version).replace("{HASHES}", info)
                                    .replace("{PATCH}", patch.name), encoding="utf-8", newline="\r\n")
    with zipfile.ZipFile(z, "w", zipfile.ZIP_STORED) as zf:
        for f in sorted(rel.iterdir()):
            zf.write(f, f.name)
    print(z, f"patch sha1 {hashes(patch)['sha1']}")


if __name__ == "__main__":
    main()
