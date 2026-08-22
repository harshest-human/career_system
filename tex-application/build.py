"""Build every CV and cover-letter entry point with XeLaTeX."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "build"
DOCUMENTS = (
    "cv-en.tex",
    "cover-letter-en.tex",
    "cv-de.tex",
    "cover-letter-de.tex",
)


def main() -> int:
    engine = shutil.which("xelatex")
    if not engine:
        print("Error: xelatex was not found on PATH.", file=sys.stderr)
        return 1

    OUTPUT.mkdir(exist_ok=True)
    for document in DOCUMENTS:
        print(f"Building {document}", flush=True)
        command = [
            engine,
            "-interaction=nonstopmode",
            "-halt-on-error",
            f"-output-directory={OUTPUT}",
            str(ROOT / document),
        ]
        for pass_number in (1, 2):
            try:
                result = subprocess.run(
                    command,
                    cwd=ROOT,
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=90,
                )
            except subprocess.TimeoutExpired:
                print(
                    f"Error: {document} timed out on pass {pass_number}. "
                    "MiKTeX may be waiting to install a package.",
                    file=sys.stderr,
                )
                return 1
            if result.returncode:
                print(result.stdout, file=sys.stderr)
                return result.returncode

    print(f"PDFs created in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

