"""check.py: the repo's one-command check. The pre-commit hook runs it; exit code gates commits.

    python -X utf8 tools/check.py

1. tests (tests/test_english_build.py builds the English from script/ into a temp tree: fit, EXE romdiff with
   the write journal, tools/gate.py on the archives);
2. text lint over the whole script (`batches.py lint`: width, pages, control codes, glossary, stub lines)."""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PY = [sys.executable, "-X", "utf8"]

# no:faulthandler - unicorn's handled SEH faults (tests/test_asm.py) print as crashes otherwise
rc = subprocess.call(PY + ["-m", "pytest", "-q", "-p", "no:faulthandler", str(ROOT / "tests")], cwd=ROOT)
rc = rc or subprocess.call(PY + [str(ROOT / "tools" / "batches.py"), "lint"], cwd=ROOT)
sys.exit(rc)
