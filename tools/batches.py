"""batches.py: translation units, batch files, checks and merge (phase 6).

    python -X utf8 tools/batches.py split [--chars 3500]   # new work/tl/bNNN.tsv + build/terms_bNNN.txt
    python -X utf8 tools/batches.py check bNNN              # validate work/tl/bNNN.out.tsv; prints OK
    python -X utf8 tools/batches.py merge bNNN [...]        # check, then write the English into script/
    python -X utf8 tools/batches.py fit FORM "text" [--speaker]   # wrapped preview (dlg|narration|vis|desc)
    python -X utf8 tools/batches.py names                   # fill speaker-label entries from glossary.md
    python -X utf8 tools/batches.py pairs bNNN              # reviewer file work/tl/bNNN.pairs.txt
    python -X utf8 tools/batches.py stats                   # translated / total units

A *unit* is what a translator writes once (docs/re/text.md, "English format"):
- SCN box: consecutive message ops up to the one that ends the page (\\f); the English is one paragraph, stored
  in the box's first dialogue entry (`en`); the other entries of the box get status "box". Insert (phase 7)
  wraps it and spreads the lines over the box's ops. A leading speaker-label op ("カイエス\\n") is its own unit
  of form "name", filled from glossary.md's speaker table (`names`), never batched.
- MES page (VIS caption): the speaker line is dropped from the JP shown; the English is the caption text only.
- Single strings (choice options, banners, SMX names/descriptions, EXE labels): one entry each.
"""
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "script"
TL = ROOT / "work" / "tl"
BUILD = ROOT / "build"
GLOSSARY = ROOT / "glossary.md"

ESC = re.compile(r"\\(?:[a-zA-Z]\d*|x[0-9a-fA-F]{2})")
TAIL = re.compile(r"(\\[nf])+$")
NAME_RE = re.compile(r"^[^\s\u3000「」『』（）()・。、！？…ー〜~]{1,10}$|^[^\s\u3000「」『』（）()。、！？]{1,12}$")
OPEN = ("「", "『", "（", "\u3000「", "  「")
WIDTH = {"msg": 28, "vis": 62, "desc": 22}
PAGE_LINES = 4
LIMIT = {"dlg": 3 * 4 * 28, "narration": 3 * 4 * 28, "cont": 3 * 4 * 28, "vis": 4 * 62, "name": 18, "item": 18, "desc": 44, "menu": 6, "sys": 26}
HONORIFICS = {"さん": "-san", "様": "-sama", "さま": "-sama", "くん": "-kun", "君": "-kun", "ちゃん": "-chan",
              "殿": "-dono"}


def load_files():
    out = []
    for path in sorted(SCRIPT.rglob("*.json")):
        out.append((path, json.loads(path.read_text(encoding="utf-8"))))
    return out


def strip(jp):
    """JP text as a translator sees it: escapes gone, line indents trimmed."""
    lines = [ESC.sub("", x).strip(" \u3000") for x in jp.split("\\n")]
    return " / ".join(x for x in lines if x)


def tail(jp):
    m = TAIL.search(jp)
    return m.group(0) if m else ""


def is_name(e, nxt):
    text = e["jp"][:-2] if e["jp"].endswith("\\n") else None
    if not (text and nxt and NAME_RE.match(text) and nxt["jp"].startswith(OPEN)):
        return False
    # 《磐舟》 / カイエスの刀 + （reading）... are book and equipment headers, not speakers
    return not (nxt["jp"].startswith("（") and (text.startswith("《") or "の" in text))


def units():
    """Every translation unit in story-file order: dicts with id, ids, file, form, speaker (JP), jp, limit."""
    res = []
    for path, data in load_files():
        es = data["entries"]
        kind = path.parent.name if path.parent != SCRIPT else "exe"
        rel = path.relative_to(SCRIPT).as_posix()
        if kind == "scn":
            box, pending = [], [""]

            def close(nxt):
                if not box:
                    return
                speaker, pending[0] = pending[0], ""
                if len(box) > 1 and is_name(box[0], box[1]) or len(box) == 1 and is_name(box[0], nxt):
                    # a name label; when another op (an item gain, a sound) sits between it and the speech, the
                    # label closes a box by itself and names the next one
                    name = box.pop(0)
                    speaker = name["jp"][:-2]
                    res.append(dict(id=name["id"], ids=[name["id"]], file=rel, form="name", speaker="",
                                    jp=speaker, limit=18))
                    if not box:
                        pending[0] = speaker
                        return
                if len(box) == 1 and not tail(box[0]["jp"]) and (
                        "no message op" in box[0]["notes"] or box[0]["jp"].startswith("\\x")):
                    # data runs (choice options, place-name banners): fixed byte length until phase 7
                    e = box[0]
                    form = "banner" if e["jp"].startswith("\\x") else "choice"
                    res.append(dict(id=e["id"], ids=[e["id"]], file=rel, form=form, speaker=speaker,
                                    jp=strip(e["jp"]), limit=e["len"]))
                else:
                    form = "dlg" if speaker else "narration"
                    last = res[-1] if res and res[-1]["file"] == rel else None
                    if (not speaker and last and last["form"] in ("dlg", "cont")
                            and not box[0]["jp"].startswith(OPEN) and not last["jp"].endswith(("」", "』", "）"))):
                        # the next page of a speech that runs over a page break: no name label on screen
                        form, speaker = "cont", last["speaker"]
                    res.append(dict(id=box[0]["id"], ids=[e["id"] for e in box], file=rel,
                                    form=form, speaker=speaker,
                                    jp=" / ".join(strip(e["jp"]) for e in box), limit=LIMIT["dlg"]))
                box.clear()

            prev = None
            for e in es:
                if prev is not None:
                    gap = int(e["ptr"], 16) - (int(prev["ptr"], 16) + prev["len"])
                    if prev["jp"].endswith("\\f") or not tail(prev["jp"]) or gap > 4 or not tail(e["jp"]):
                        close(e)
                box.append(e)
                prev = e
            close(None)
        elif kind == "mes":
            for e in es:
                lines = e["jp"].split("\\n")
                speaker = lines[0] if len(lines) > 2 and NAME_RE.match(lines[0]) else ""
                body = "\\n".join(lines[1:]) if speaker else e["jp"]
                res.append(dict(id=e["id"], ids=[e["id"]], file=rel, form="vis", speaker=speaker,
                                jp=strip(body), limit=LIMIT["vis"]))
        else:
            for e in es:
                if kind == "exe":
                    form = "menu" if int(e["ptr"], 16) >= 0x78C0C else "sys"
                else:
                    form = "desc" if e["len"] > 18 or "。" in e["jp"] else "item"
                res.append(dict(id=e["id"], ids=[e["id"]], file=rel, form=form, speaker="",
                                jp=e["jp"], limit=LIMIT[form]))
    return res


# ---------------------------------------------------------------- glossary

def glossary():
    """(rows, speakers): rows = [(section, jp, en, avoid)], speakers = {jp label: en}."""
    rows, speakers, section = [], {}, ""
    for line in GLOSSARY.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            section = line[3:].strip()
            continue
        if not line.startswith("|") or line.startswith("|---") or line.startswith("| JP"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or not cells[0] or not cells[1] or cells[0].startswith("<"):
            continue
        if section.startswith("Speaker"):
            speakers[cells[0]] = cells[1]
        else:
            rows.append((section, cells[0], cells[1], cells[4] if len(cells) > 4 else ""))
    return rows, speakers


def kana_runs(text):
    return re.findall(r"[\u30a0-\u30ffー・]+|[\u4e00-\u9fff々]+|[\u3040-\u309f]+", text)


def term_hit(jp_term, jp):
    """Whole-run match: the term must not sit inside a longer katakana word (ミン inside タイミング)."""
    for m in re.finditer(re.escape(jp_term), jp):
        a, b = m.start(), m.end()
        kata = re.compile(r"[\u30a0-\u30ffー]")
        if kata.match(jp_term[0]) and a > 0 and kata.match(jp[a - 1]):
            continue
        if kata.match(jp_term[-1]) and b < len(jp) and kata.match(jp[b]) and jp[b] != "・":
            continue
        return True
    return False


# ---------------------------------------------------------------- wrapping

def wrap(text, width):
    return textwrap.wrap(text, width, break_long_words=True, break_on_hyphens=False) or [""]


def pages(text, speaker):
    """Field box: 28 chars a line, 27 on a page's last line (page mark), 4 lines a page, the speaker label is the
    first page's first line. Returns the list of pages (lists of lines)."""
    words, out, page, line = text.split(), [], [], ""
    room = PAGE_LINES - (1 if speaker else 0)

    def width():
        return WIDTH["msg"] - (1 if len(page) == room - 1 else 0)

    for w in words:
        cand = (line + " " + w) if line else w
        if len(cand) <= width():
            line = cand
            continue
        if line:
            page.append(line)
            if len(page) == room:
                out.append(page)
                page, room = [], PAGE_LINES
        while len(w) > width():
            page.append(w[:width()])
            w = w[width():]
        line = w
    if line or not out:
        page.append(line)
    if page:
        out.append(page)
    return out


def preview(form, text, speaker=False):
    if form in ("dlg", "narration", "cont"):
        return pages(text, form == "dlg")
    if form == "vis":
        return [wrap(text, WIDTH["vis"])]
    if form == "desc":
        return [wrap(text, WIDTH["desc"])]
    return [[text]]


# ---------------------------------------------------------------- batches

def batch_path(b, suffix):
    return TL / f"{b}{suffix}"


def done_ids():
    out = set()
    for path, data in load_files():
        for e in data["entries"]:
            if e.get("en"):
                out.add(e["id"])
    return out


def split(chars=3500, only=None, label=None):
    """Batch every untranslated unit; `only` = file-name substring and `label` = batch name (pilot slices)."""
    TL.mkdir(parents=True, exist_ok=True)
    BUILD.mkdir(exist_ok=True)
    have = sorted(int(p.stem[1:4]) for p in TL.glob("b[0-9][0-9][0-9].tsv"))
    queued = set()
    for p in TL.glob("*.tsv"):
        if p.name.endswith(".out.tsv"):
            continue
        queued |= {line.split("\t")[0] for line in p.read_text(encoding="utf-8").splitlines() if line}
    nxt = (have[-1] + 1) if have else 1
    done = done_ids()
    rows, speakers = glossary()
    todo = [u for u in units() if u["form"] != "name" and u["jp"].strip() and u["id"] not in done
            and u["id"] not in queued and (not only or only in u["file"])]
    if label:
        chars = 10 ** 9
    batches, cur, size = [], [], 0
    for u in todo:
        n = len(u["jp"])
        # prefer to close a batch at a file boundary once it is three quarters full
        if cur and (size + n > chars or (size > chars * 0.75 and u["file"] != cur[-1]["file"])):
            batches.append(cur)
            cur, size = [], 0
        cur.append(u)
        size += n
    if cur:
        batches.append(cur)
    made = []
    for i, b in enumerate(batches):
        name = label or f"b{nxt + i:03d}"
        p = batch_path(name, ".tsv")
        if p.exists():
            sys.exit(f"{p} exists; refusing to overwrite")
        lines = []
        for u in b:
            sp = speakers.get(u["speaker"], u["speaker"]) if u["speaker"] else ""
            lim = {"dlg": "2pg", "narration": "2pg", "cont": "2pg", "vis": "4ln", "desc": "2ln"}.get(
                u["form"], f"{u['limit']}ch")
            lines.append("\t".join([u["id"], sp, u["form"], lim, u["jp"]]))
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        alljp = "".join(u["jp"] for u in b)
        terms = [f"{jp}\t{en}\t{sec}" + (f"\tAVOID {av}" if av else "") for sec, jp, en, av in rows
                 if term_hit(jp, alljp)]
        (BUILD / f"terms_{name}.txt").write_text("\n".join(terms) + "\n", encoding="utf-8")
        made.append((name, len(b), len(alljp), b[0]["file"], b[-1]["file"]))
    for m in made:
        print("%s: %d units, %d JP chars, %s .. %s" % m)
    print(f"{len(made)} batches")


def read_batch(b):
    rows = []
    for line in batch_path(b, ".tsv").read_text(encoding="utf-8").splitlines():
        if line:
            i, sp, form, lim, jp = line.split("\t")
            rows.append(dict(id=i, speaker=sp, form=form, limit=int(lim[:-2]), jp=jp))
    return rows


def read_out(b):
    p = batch_path(b, ".out.tsv")
    out, problems = {}, []
    if not p.exists():
        return out, [f"{p.name} missing"]
    for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        if "\t" not in line:
            problems.append(f"line {n}: no tab")
            continue
        i, en = line.split("\t", 1)
        if i in out:
            problems.append(f"{i}: duplicate id")
        out[i] = en
    return out, problems


def check_unit(u, en, rows):
    errs, warns = [], []
    if not en.strip():
        errs.append("empty")
    if "\t" in en:
        errs.append("tab inside the English")
    bad = sorted({c for c in en if not (32 <= ord(c) < 127)})
    if bad:
        errs.append("non-ASCII: " + "".join(bad))
    if re.search(r"\\u[0-9a-fA-F]{4}", en):
        errs.append("\\uXXXX escape")
    if "@" in en:
        errs.append("'@' is a renderer control; write 'at'")
    if "  " in en:
        errs.append("double space (the renderer draws it as a wide space)")
    if en != en.strip():
        errs.append("leading/trailing space")
    if u["form"] in ("menu", "sys", "item", "desc", "choice", "banner"):
        if sorted(ESC.findall(en)) != sorted(ESC.findall(u["jp"])):
            errs.append(f"escape codes differ from the JP: {ESC.findall(u['jp'])}")
    elif "\\" in en:
        errs.append("backslash: write plain text; breaks and pages are added at insert")
    if re.search(r"\d(st|nd|rd|th)\b", en) and re.search(r"[0-9０-９]", u["jp"]) is None:
        warns.append("ordinal suffix")
    plain = ESC.sub("", en)
    form = u["form"]
    if form in ("dlg", "narration", "cont"):
        pg = pages(plain, form == "dlg")
        if len(pg) > 3:
            errs.append(f"{len(pg)} pages (max 3; see `batches.py fit`)")
        elif len(pg) > 2:
            warns.append(f"{len(pg)} pages")
        if len(pg) > 1 and len(pg[-1]) == 1 and len(pg[-1][0]) < 14:
            warns.append(f"stub page '{pg[-1][0]}': rephrase or move words to the next unit")
    elif form == "vis":
        n = len(wrap(plain, WIDTH["vis"]))
        if n > 4:
            errs.append(f"{n} caption lines at 62 chars (max 4)")
    elif form == "desc":
        n = len(wrap(plain, WIDTH["desc"]))
        if n > 2:
            errs.append(f"{n} lines at 22 chars (max 2)")
    elif len(plain) > u["limit"]:
        errs.append(f"{len(plain)} chars > {u['limit']}")
    for sec, jp, gen, avoid in rows:
        if not term_hit(jp, u["jp"]):
            continue
        forms = [x.strip() for x in gen.split("/")]
        if not any(f.lower() in en.lower() for f in forms):
            # proper names (katakana) are binding; generic place words (関所, 湿原) only warn
            hard = sec in ("Characters", "Places") and re.search(r"[゠-ヿ]", jp)
            (errs if hard else warns).append(f"glossary: {jp} -> {gen}")
        for a in [x.strip() for x in avoid.split(",") if x.strip()]:
            if re.search(r"\b" + re.escape(a) + r"\b", en):
                errs.append(f"glossary avoid: {a}")
        for h, eh in HONORIFICS.items():
            if sec == "Characters" and (jp + h) in u["jp"] and not any(f + eh in en for f in forms):
                errs.append(f"honorific: {jp}{h} -> {forms[0]}{eh}")
    return errs, warns


def check(b, quiet=False):
    rows, _ = glossary()
    batch = read_batch(b)
    out, problems = read_out(b)
    want = [u["id"] for u in batch]
    for i in want:
        if i not in out:
            problems.append(f"{i}: missing")
    for i in out:
        if i not in set(want):
            problems.append(f"{i}: not in the batch")
    warns = []
    for u in batch:
        if u["id"] in out:
            e, w = check_unit(u, out[u["id"]], rows)
            problems += [f"{u['id']}: {x}" for x in e]
            warns += [f"{u['id']}: {x}" for x in w]
    if not quiet:
        for w in warns:
            print("warn", w)
        for p in problems:
            print("ERROR", p)
        print("OK" if not problems else f"{len(problems)} errors")
    return not problems


def names():
    _, speakers = glossary()
    missing = {}
    edits = {}
    for u in units():
        if u["form"] != "name":
            continue
        if u["jp"] in speakers:
            edits[u["id"]] = speakers[u["jp"]]
        else:
            missing[u["jp"]] = missing.get(u["jp"], 0) + 1
    write_en(edits, status="tl")
    print(f"{len(edits)} speaker labels filled")
    for k, v in sorted(missing.items(), key=lambda x: -x[1]):
        print(f"missing: {k} ({v})")


def write_en(edits, status="tl", box=None):
    """Set en/status for entry ids: one structured JSON load/dump per file (never a text replace)."""
    box = box or {}
    for path, data in load_files():
        hit = False
        for e in data["entries"]:
            if e["id"] in edits:
                e["en"], e["status"] = edits[e["id"]], status
                hit = True
            elif e["id"] in box:
                e["en"], e["status"], e["notes"] = "", "box", f"box: English in {box[e['id']]}"
                hit = True
        if hit:
            path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def pairs(b):
    """Reviewer input: every unit in story order (the neighbours are the context)."""
    out, _ = read_out(b)
    lines = []
    for u in read_batch(b):
        lines.append(f">> {u['id']} | {u['speaker'] or '-'} | {u['form']} | {u['jp']}")
        lines.append(f"   EN: {out.get(u['id'], '')}")
    batch_path(b, ".pairs.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(batch_path(b, ".pairs.txt"))


def story(parts=3):
    """Story-order JP (and any English) in `parts` files: work/tl/story/partN.txt, for the synopsis and terms."""
    us = [u for u in units() if u["form"] not in ("name",) and u["jp"].strip()]
    en = {}
    for _p, data in load_files():
        for e in data["entries"]:
            if e.get("en"):
                en[e["id"]] = e["en"]
    total = sum(len(u["jp"]) for u in us)
    out, cur, size, last = [], [], 0, None
    for u in us:
        if u["file"] != last and size > total / parts and len(out) < parts - 1:
            out.append(cur)
            cur, size = [], 0
        if u["file"] != last:
            cur.append(f"\n## {u['file']}")
            last = u["file"]
        cur.append(f"{u['id']} | {u['speaker'] or '-'} | {u['jp']}" + (f"\n    EN: {en[u['id']]}" if u["id"] in en else ""))
        size += len(u["jp"])
    out.append(cur)
    d = TL / "story"
    d.mkdir(parents=True, exist_ok=True)
    for n, part in enumerate(out, 1):
        (d / f"part{n}.txt").write_text("\n".join(part) + "\n", encoding="utf-8")
        print(d / f"part{n}.txt", part[0].strip(), "..", [x for x in part if x.startswith("\n##")][-1].strip())


def stats():
    us = [u for u in units() if u["jp"].strip()]
    done = done_ids()
    by = {}
    for u in us:
        t = by.setdefault(u["form"], [0, 0])
        t[1] += 1
        t[0] += u["id"] in done
    for k, (a, n) in sorted(by.items()):
        print(f"{k:10} {a:6}/{n}")
    print(f"total {sum(a for a, _ in by.values())}/{sum(n for _, n in by.values())} units")


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    cmd = argv[0]
    if cmd == "split":
        opt = {k: argv[argv.index(k) + 1] for k in ("--chars", "--only", "--name") if k in argv}
        split(int(opt.get("--chars", 3500)), opt.get("--only"), opt.get("--name"))
    elif cmd == "check":
        return 0 if all([check(b) for b in argv[1:]]) else 1
    elif cmd == "merge":
        for b in argv[1:]:
            if not check(b, quiet=True):
                check(b)
                print(f"{b}: check failed, not merged")
                return 1
            out, _ = read_out(b)
            unit = {u["id"]: u for u in units()}
            edits, box = {}, {}
            for i, en in out.items():
                edits[i] = en
                for eid in unit[i]["ids"][1:]:
                    box[eid] = i
            write_en(edits, "tl", box)
            print(f"{b}: merged {len(out)} units")
    elif cmd == "fit":
        form, text = argv[1], argv[2]
        for n, pg in enumerate(preview(form, text, "--speaker" in argv), 1):
            print(f"-- page {n}")
            for line in pg:
                print(f"|{line}|  {len(line)}")
    elif cmd == "names":
        names()
    elif cmd == "pairs":
        for b in argv[1:]:
            pairs(b)
    elif cmd == "stats":
        stats()
    elif cmd == "story":
        story(int(argv[1]) if len(argv) > 1 else 3)
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
