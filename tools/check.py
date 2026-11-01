"""check.py: the repo's one-command check (tests + text lint). The pre-commit hook runs it; exit code gates commits.

    python -X utf8 tools/check.py"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# no:faulthandler - unicorn's handled SEH faults (tests/test_asm.py) print as crashes otherwise
sys.exit(subprocess.call([sys.executable, "-X", "utf8", "-m", "pytest", "-q", "-p", "no:faulthandler",
                          str(ROOT / "tests")], cwd=ROOT))
