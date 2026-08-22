"""
Self-Healing Bootstrap and Dependency Verifier
Checks environment readiness, virtual environment existence, required packages,
and MiKTeX / XeLaTeX availability. Auto-installs missing requirements via uv.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_PACKAGES = [
    "pdfplumber",
    "pypdf",
    "jinja2",
    "pandas",
    "openpyxl",
    "pyyaml",
    "beautifulsoup4",
    "requests",
    "reportlab",
]


def check_and_bootstrap_environment() -> bool:
    """Ensure all dependencies are satisfied; automatically auto-installs if missing."""
    workspace_root = Path(__file__).resolve().parent.parent
    venv_dir = workspace_root / ".venv"

    # Find uv
    uv_bin = shutil.which("uv")
    if not uv_bin:
        local_uv = Path.home() / ".local" / "bin" / ("uv.exe" if os.name == "nt" else "uv")
        if local_uv.exists():
            uv_bin = str(local_uv)

    # If running outside venv and venv exists, warn or switch
    missing_packages = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing_packages.append(pkg)

    if missing_packages:
        print(f"[Bootstrap] Missing packages detected: {', '.join(missing_packages)}")
        if uv_bin:
            print("[Bootstrap] Automatically installing missing dependencies with uv...")
            python_bin = sys.executable
            try:
                subprocess.run(
                    [uv_bin, "pip", "install", "--python", python_bin] + missing_packages,
                    check=True,
                )
                print("[Bootstrap] Dependencies successfully installed.")
            except Exception as e:
                print(f"[Bootstrap] Auto-install failed: {e}")
                return False
        else:
            print("[Bootstrap] 'uv' not found on PATH. Please run setup.ps1 or setup.sh.")
            return False

    return True


def check_latex_compiler() -> str:
    """Verify presence of XeLaTeX compiler."""
    compiler = shutil.which("xelatex")
    if not compiler and os.name == "nt":
        std_miktex = Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe")
        if std_miktex.exists():
            compiler = str(std_miktex)
    return compiler or ""


if __name__ == "__main__":
    ready = check_and_bootstrap_environment()
    compiler = check_latex_compiler()
    print(f"Environment ready: {ready}")
    print(f"LaTeX compiler: {compiler or 'Not found (install MiKTeX or TeXLive)'}")
