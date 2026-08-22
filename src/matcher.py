"""
Candidate Matching & Tabular Analysis Engine
Computes match scores, skill overlap, and gap analysis for multiple candidate profiles,
and exports structured analysis into job_analysis/job_matrix.xlsx and job_matrix.csv.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import yaml


class CandidateMatcher:
    def __init__(self, profiles_dir: Optional[Path] = None):
        self.profiles_dir = Path(profiles_dir) if profiles_dir else Path(__file__).resolve().parent.parent / "profiles"
        self.profiles: Dict[str, Dict[str, Any]] = self._load_profiles()

    def _load_profiles(self) -> Dict[str, Dict[str, Any]]:
        loaded = {}
        # 1. Load from YAML files
        if self.profiles_dir.exists():
            for profile_folder in self.profiles_dir.iterdir():
                if profile_folder.is_dir():
                    profile_file = profile_folder / "profile.yaml"
                    if profile_file.exists():
                        try:
                            with open(profile_file, "r", encoding="utf-8") as f:
                                data = yaml.safe_load(f)
                                if data:
                                    loaded[profile_folder.name] = data
                        except Exception:
                            pass

        # 2. Augment from SQLite database if available
        try:
            from src.database import Database
            db = Database()
            db_profs = db.get_all_profiles()
            for p in db_profs:
                pid = p.get("id")
                if pid and p.get("data"):
                    loaded[pid] = p["data"]
        except Exception:
            pass

        return loaded

    def compute_match(self, candidate_id: str, job_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compute keyword overlap, matched domains, and match percentage."""
        profile = self.profiles.get(candidate_id, {})
        if not profile:
            return {"match_score": 0, "matched_skills": [], "missing_skills": []}

        # Collect candidate keyword pool
        cand_keywords = set()
        skills = profile.get("skills", {})
        for domain in skills.get("domains", []):
            cand_keywords.update(domain.lower().replace("(", "").replace(")", "").split())
        for hw in skills.get("hardware_instruments", []):
            cand_keywords.update(hw.lower().replace("(", "").replace(")", "").split())
        for sw in skills.get("software_tools", []):
            cand_keywords.update(sw.lower().replace("(", "").replace(")", "").split())

        job_skills = set(job_data.get("extracted_skills", []))
        matched = []
        missing = []

        for skill in job_skills:
            skill_tokens = set(skill.lower().split())
            if skill_tokens.intersection(cand_keywords) or skill.lower() in " ".join(cand_keywords):
                matched.append(skill)
            else:
                missing.append(skill)

        # Baseline score based on matches
        total_skills = len(job_skills)
        if total_skills == 0:
            score = 65  # Base neutral score when no specific skills detected
        else:
            score = int((len(matched) / total_skills) * 100)
            score = max(20, min(98, score))

        return {
            "match_score": score,
            "matched_skills": matched,
            "missing_skills": missing,
        }

    def generate_matrix(self, jobs: List[Dict[str, Any]], output_dir: Path = Path("job_analysis")) -> Path:
        """Create tabular CSV and styled Excel workbook comparing all jobs across candidates."""
        output_dir.mkdir(parents=True, exist_ok=True)

        rows = []
        for job in jobs:
            base_row = {
                "Company": job.get("company", ""),
                "Role Title": job.get("role_title", ""),
                "Location": job.get("location", ""),
                "Application Deadline": job.get("deadline", ""),
                "Target Start": job.get("start_date", ""),
                "Contract Type": job.get("contract_type", ""),
                "Required Languages": job.get("languages", ""),
                "Extracted Skills": ", ".join(job.get("extracted_skills", [])),
                "Contact Email": job.get("contact_email", ""),
                "Source File": job.get("source_file", ""),
            }

            # Evaluate each profile
            for cand_id, cand_data in self.profiles.items():
                cand_name = cand_data.get("personal", {}).get("full_name", cand_id.capitalize())
                res = self.compute_match(cand_id, job)
                base_row[f"Fit Score ({cand_name})"] = f"{res['match_score']}%"
                base_row[f"Matched Skills ({cand_name})"] = ", ".join(res["matched_skills"])

            rows.append(base_row)

        df = pd.DataFrame(rows)
        csv_path = output_dir / "job_matrix.csv"
        xlsx_path = output_dir / "job_matrix.xlsx"

        df.to_csv(csv_path, index=False, encoding="utf-8-sig")

        # Save to Excel with openpyxl formatting
        with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Job Matrix", index=False)
            ws = writer.sheets["Job Matrix"]

            # Auto-adjust column widths
            for col in ws.columns:
                max_len = max(len(str(cell.value or "")) for cell in col)
                col_letter = col[0].column_letter
                ws.column_dimensions[col_letter].width = min(40, max(12, max_len + 3))

        print(f"[Matcher] Generated job analysis matrix:\n  - CSV:   {csv_path}\n  - Excel: {xlsx_path}")
        return xlsx_path
