"""Build the C-Lock CV and cover letter with XeLaTeX."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "build"
DOCUMENTS = ("cv.tex", "cover-letter.tex")


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
                print(f"Error: {document} timed out on pass {pass_number}.", file=sys.stderr)
                return 1
            if result.returncode:
                print(result.stdout, file=sys.stderr)
                return result.returncode

        pdf = OUTPUT / f"{Path(document).stem}.pdf"
        if not pdf.exists() or pdf.stat().st_size < 1_000 or not pdf.read_bytes().startswith(b"%PDF"):
            print(f"Error: XeLaTeX did not create a valid PDF for {document}.", file=sys.stderr)
            return 1

    print(f"PDFs created in {OUTPUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
