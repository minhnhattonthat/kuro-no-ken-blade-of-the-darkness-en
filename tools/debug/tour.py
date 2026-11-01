"""tour.py: warp to every scene in tools/debug/scenes.lua and collect proof shots.

    python -X utf8 tools/debug/tour.py [--cue build/kuro_en.cue] [--only 06blk_1,03ysk_0] [--jobs 3] [--states]
                                       [--keep-base]

The first scene runs from a cold boot (tools/routes/boot.txt + tools/debug/warp.lua, through the new-game intro,
~18000 frames) and saves work/states/base_<cue>.sstate where the intro ends; every other scene starts from that
state (same warp.lua path from there). Output in work/qa/tour/:
<scene>/ (run dir), <scene>.png (proof shot), report.tsv (scene, ok, slots, map), sheet*.png.
--states also writes work/states/<scene>.sstate at the proof shot (regenerate after engine/font/graphics
changes). Exit 1 if any scene's proof is not ok.
"""
import argparse
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill import SKILL  # noqa: E402

DEBUG = Path(__file__).resolve().parent


def scene_names(cue, out):
    """Scene names in scenes.lua order, as warp.lua lists them (SCENE='list'; scenes.lua builds names in loops)."""
    d = out / "_list"
    subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(cue), "--out", str(d),
                    "--script", "tools/debug/warp.lua", "--var", "SCENE='list'", "--frames", "60"],
                   capture_output=True, text=True)
    names = re.findall(r"^scene (\S+)$", (d / "log.txt").read_text(encoding="utf-8"), re.M)
    if not names:
        sys.exit(f"no scene list: see {d}/log.txt")
    return names


def run(cue, scene, out, frames, states, base, cold):
    d = out / scene
    cmd = [sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "emu.py"), str(cue), "--out", str(d),
           "--script", "tools/debug/warp.lua", "--var", f"SCENE='{scene}'", "--frames", str(frames),
           "--timeout", "900"]
    cmd += ["--route", "tools/routes/boot.txt", "--var", f"BASE=[[{base.resolve().as_posix()}]]"] if cold \
        else ["--state-in", str(base)]
    if states:
        Path("work/states").mkdir(parents=True, exist_ok=True)
        cmd += ["--var", f"STATE=[[{Path('work/states').resolve().as_posix()}/{scene}.sstate]]"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    log = (d / "log.txt").read_text(encoding="utf-8", errors="replace") if (d / "log.txt").exists() else ""
    m = re.search(r"proof (ok|FAIL) at frame \d+ slots (\S*) map (\S*)", log)
    if (d / "proof.png").exists():
        shutil.copy(d / "proof.png", out / f"{scene}.png")
    ok = bool(m and m.group(1) == "ok" and r.returncode == 0)
    return scene, ok, (m.group(2) if m else f"no proof (emu exit {r.returncode})"), (m.group(3) if m else "")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cue", default="build/kuro_en.cue")
    ap.add_argument("--only", default="")
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--frames", type=int, default=40000)   # warp.lua ends each run at its proof shot
    ap.add_argument("--out", default="work/qa/tour")
    ap.add_argument("--states", action="store_true")
    ap.add_argument("--keep-base", action="store_true", help="reuse work/states/base_<cue>.sstate (same build only)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names = scene_names(a.cue, out)
    if a.only:
        want = a.only.split(",")
        names = [n for n in names if n in want]
    base = Path("work/states") / f"base_{Path(a.cue).stem}.sstate"
    base.parent.mkdir(parents=True, exist_ok=True)
    results = []
    if not (a.keep_base and base.exists()):
        base.unlink(missing_ok=True)
        results = [run(a.cue, names[0], out, a.frames, a.states, base, True)]   # cold boot, writes the base state
        names = names[1:]
        if not base.exists():
            sys.exit(f"cold boot run made no base state: see {out / results[0][0]}/log.txt")
    with ThreadPoolExecutor(a.jobs) as ex:
        results += list(ex.map(lambda s: run(a.cue, s, out, a.frames, a.states, base, False), names))
    with open(out / "report.tsv", "w", encoding="utf-8", newline="\n") as f:
        f.write("scene\tok\tslots\tmap\n")
        for s, ok, slots, m in results:
            f.write(f"{s}\t{'ok' if ok else 'FAIL'}\t{slots}\t{m}\n")
    pngs = [str(out / f"{s}.png") for s, *_ in results if (out / f"{s}.png").exists()]
    if pngs:
        subprocess.run([sys.executable, "-X", "utf8", str(Path(SKILL) / "scripts" / "sheet.py"), *pngs,
                        "--out", str(out / "sheet.png")])
    bad = [s for s, ok, *_ in results if not ok]
    print(f"{len(results) - len(bad)}/{len(results)} ok" + (f"; FAIL: {', '.join(bad)}" if bad else ""))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
