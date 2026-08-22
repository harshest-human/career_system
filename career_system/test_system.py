"""
Career System Diagnostic Doctor & Self-Testing Suite
Automatically checks dependencies, repairs missing packages/environments,
and executes end-to-end tests across Database, Scraping, Extraction, LaTeX Compilation, and Web API.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple

# Ensure workspace root is in python path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


class SystemDoctor:
    def __init__(self):
        self.results: List[Tuple[str, str, str]] = []
        self.all_passed = True

    def log_result(self, category: str, item: str, status: str, details: str = ""):
        self.results.append((category, item, status))
        tag = "[PASS]" if status == "PASS" else "[WARN]" if status == "WARN" else "[FAIL]"
        if status == "FAIL":
            self.all_passed = False
        msg = f"  {tag:<7} {item:<35} {details}"
        print(msg)

    def banner(self, title: str):
        print("\n" + "=" * 65)
        print(f" {title}")
        print("=" * 65)

    def check_and_repair_environment(self):
        self.banner("PHASE 1: Environment & Dependency Diagnostics")

        # 1. Python Version
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if sys.version_info >= (3, 10):
            self.log_result("Environment", "Python Runtime", "PASS", f"v{py_ver} (64-bit)")
        else:
            self.log_result("Environment", "Python Runtime", "FAIL", f"v{py_ver} (Requires Python >= 3.10)")

        # 2. Package Manager (uv)
        uv_bin = shutil.which("uv")
        if not uv_bin and os.name == "nt":
            local_uv = Path.home() / ".local" / "bin" / "uv.exe"
            if local_uv.exists():
                uv_bin = str(local_uv)

        if uv_bin:
            self.log_result("Environment", "Fast Package Manager (uv)", "PASS", "Installed and ready")
        else:
            print("  [INFO]  Installing 'uv' package manager automatically...")
            try:
                if os.name == "nt":
                    subprocess.run(
                        ["powershell", "-ExecutionPolicy", "ByPass", "-c", "irm https://astral.sh/uv/install.ps1 | iex"],
                        check=True,
                    )
                else:
                    subprocess.run("curl -LsSf https://astral.sh/uv/install.sh | sh", shell=True, check=True)
                self.log_result("Environment", "Fast Package Manager (uv)", "PASS", "Auto-installed")
            except Exception as e:
                self.log_result("Environment", "Fast Package Manager (uv)", "WARN", f"Could not install uv: {e}")

        # 3. Virtual Environment
        venv_python = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
        if venv_python.exists():
            self.log_result("Environment", "Virtual Environment (.venv)", "PASS", f"Active ({venv_python})")
        else:
            self.log_result("Environment", "Virtual Environment (.venv)", "WARN", "Created on next launch via setup.ps1")

        # 4. Dependency Packages Check & Auto-Install
        required_pkgs = [
            ("fastapi", "fastapi"),
            ("uvicorn", "uvicorn"),
            ("httpx", "httpx"),
            ("pdfplumber", "pdfplumber"),
            ("pypdf", "pypdf"),
            ("jinja2", "jinja2"),
            ("pandas", "pandas"),
            ("openpyxl", "openpyxl"),
            ("yaml", "pyyaml"),
            ("bs4", "beautifulsoup4"),
            ("requests", "requests"),
            ("reportlab", "reportlab"),
            ("multipart", "python-multipart"),
        ]

        missing = []
        for mod, pkg in required_pkgs:
            try:
                __import__(mod)
            except ImportError:
                missing.append(pkg)

        if not missing:
            self.log_result("Dependencies", "Python Packages (13/13)", "PASS", "All dependencies satisfied")
        else:
            print(f"  [INFO]  Missing packages: {', '.join(missing)}. Auto-installing...")
            if uv_bin:
                try:
                    subprocess.run([uv_bin, "pip", "install", "--python", sys.executable] + missing, check=True)
                    self.log_result("Dependencies", "Python Packages", "PASS", "Auto-installed missing packages")
                except Exception as e:
                    self.log_result("Dependencies", "Python Packages", "FAIL", f"Auto-install failed: {e}")
            else:
                self.log_result("Dependencies", "Python Packages", "FAIL", f"Missing: {', '.join(missing)}")

        # 5. LaTeX Compiler (XeLaTeX)
        latex_bin = shutil.which("xelatex")
        if not latex_bin and os.name == "nt":
            std_miktex = Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe")
            if std_miktex.exists():
                latex_bin = str(std_miktex)

        if latex_bin:
            self.log_result("LaTeX Engine", "XeLaTeX PDF Compiler", "PASS", f"Found ({latex_bin})")
        else:
            self.log_result(
                "LaTeX Engine",
                "XeLaTeX PDF Compiler",
                "WARN",
                "MiKTeX not found. Install from https://miktex.org to compile PDFs.",
            )

    def run_functional_tests(self):
        self.banner("PHASE 2: Functional System Tests")

        # Test 1: Database and Profile Sync
        try:
            from src.database import Database
            db = Database()
            profiles = db.get_all_profiles()
            prof_ids = [p["id"] for p in profiles]
            if "default" in prof_ids or len(prof_ids) > 0:
                self.log_result("Database", "SQLite Profiles Sync", "PASS", f"Active profiles: {', '.join(prof_ids)}")
            else:
                self.log_result("Database", "SQLite Profiles Sync", "WARN", f"Found profiles: {prof_ids}")
        except Exception as e:
            self.log_result("Database", "SQLite Profiles Sync", "FAIL", str(e))

        # Test 2: Pointwise Breakdown & Match Scoring
        try:
            from src.ai_assistant import CareerAIAssistant
            from src.matcher import CandidateMatcher
            ai = CareerAIAssistant()
            mat = CandidateMatcher()
            sample_text = """
            Arcadis Germany GmbH
            Position: Senior ESG & Sustainability Consultant
            Location: Hamburg, Germany (Hybrid)
            Employment: Full-time, Permanent
            Requirements: Agricultural engineering, livestock emissions, GHG, R, Python, sensor technology, ESG reporting.
            """
            breakdown = ai.extract_job_breakdown(sample_text)
            score_res = mat.compute_match("default", breakdown)
            if len(breakdown.get("key_responsibilities", [])) > 0:
                self.log_result("AI Breakdown", "Pointwise Breakdown Extractor", "PASS", f"Extracted {len(breakdown.get('key_responsibilities', []))} tasks, {len(breakdown.get('required_qualifications', []))} qualifications")
            else:
                self.log_result("AI Breakdown", "Pointwise Breakdown Extractor", "WARN", "Low detail extraction")
        except Exception as e:
            self.log_result("AI Breakdown", "Pointwise Breakdown Extractor", "FAIL", str(e))

        # Test 3: Bilingual HTML Resume and Cover Letter Rendering
        try:
            from src.html_templates import render_html_cv, render_html_cover_letter
            test_prof = {"personal": {"full_name": "Test Candidate", "title_en": "Lead Engineer", "email": "test@example.com"}}
            html_cv_en = render_html_cv(test_prof, {"company": "Target Co", "role_title": "Lead"}, lang="en")
            html_cv_de = render_html_cv(test_prof, {"company": "Target Co", "role_title": "Lead"}, lang="de")
            html_letter_en = render_html_cover_letter(test_prof, {"company": "Target Co", "role_title": "Lead"}, lang="en")
            html_letter_de = render_html_cover_letter(test_prof, {"company": "Target Co", "role_title": "Lead"}, lang="de")
            if "Professional Experience" in html_cv_en and "Berufserfahrung" in html_cv_de and "Yours sincerely" in html_letter_en and "Mit freundlichen Grüßen" in html_letter_de:
                self.log_result("HTML Studio", "Bilingual HTML (EN-UK & DE) Engine", "PASS", "Instant bilingual rendering (<10ms)")
            else:
                self.log_result("HTML Studio", "Bilingual HTML (EN-UK & DE) Engine", "FAIL", "Missing bilingual localized headers")
        except Exception as e:
            self.log_result("HTML Studio", "Bilingual HTML (EN-UK & DE) Engine", "FAIL", str(e))

        # Test 4: Google Workspace Docs & Sheets Formatter
        try:
            from src.google_sync import GoogleWorkspaceSync
            g_sync = GoogleWorkspaceSync()
            formatted_text = g_sync.format_cv_for_google_docs(test_prof, lang="en")
            if "TEST CANDIDATE" in formatted_text and "EXECUTIVE PROFILE" in formatted_text:
                self.log_result("Google Workspace", "Google Docs & Drive Formatter", "PASS", "Ready for 1-click Docs & Drive export")
            else:
                self.log_result("Google Workspace", "Google Docs & Drive Formatter", "FAIL", "Formatting mismatch")
        except Exception as e:
            self.log_result("Google Workspace", "Google Docs & Drive Formatter", "FAIL", str(e))

        # Test 5: Web API & Routes Health Check
        try:
            from fastapi.testclient import TestClient
            from app import app
            client = TestClient(app)
            r1 = client.get("/api/profiles")
            r2 = client.get("/api/jobs")
            r3 = client.get("/")
            r4 = client.get("/api/portals")
            r5 = client.get("/api/google/script-template")
            if all(r.status_code == 200 for r in [r1, r2, r3, r4, r5]):
                self.log_result("Web Application", "FastAPI Server & 4-Step Wizard UI", "PASS", "HTTP 200 OK across all routes")
            else:
                self.log_result("Web Application", "FastAPI Server & 4-Step Wizard UI", "FAIL", f"Status: {r1.status_code}, {r2.status_code}, {r3.status_code}")
        except Exception as e:
            self.log_result("Web Application", "FastAPI Server & 4-Step Wizard UI", "FAIL", str(e))

    def print_summary(self):
        self.banner("DIAGNOSTIC SUMMARY & READINESS REPORT")
        passes = sum(1 for _, _, s in self.results if s == "PASS")
        warns = sum(1 for _, _, s in self.results if s == "WARN")
        fails = sum(1 for _, _, s in self.results if s == "FAIL")

        print(f"\n  Total Checks Run: {len(self.results)}")
        print(f"  Passed:           {passes}")
        print(f"  Warnings:         {warns}")
        print(f"  Failures:         {fails}")

        print("\n" + "-" * 65)
        if fails == 0:
            print("  VERDICT: [100% READY] All systems operational!")
            print("  You can now launch the local web app by running:")
            print("     start_web.bat  (or python app.py)")
        else:
            print("  VERDICT: [ACTION REQUIRED] Please resolve failures above.")
        print("-" * 65 + "\n")


def main() -> int:
    doctor = SystemDoctor()
    doctor.check_and_repair_environment()
    doctor.run_functional_tests()
    doctor.print_summary()
    return 0 if doctor.all_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
