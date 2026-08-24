"""
SQLite Database Layer for Career System Local Web App
Manages structured data for Profiles, Jobs, Portal Credentials, Contacts, and Outreach Logs,
with systematic nomenclature: {jobposition}_{jobID}_{companyname}_{suffix}
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


import os


def sanitize_slug(text: Any, max_len: int = 35) -> str:
    """Sanitize text to be safe across Windows/Linux filesystems."""
    text = str(text or "").strip()
    # Transliterate German umlauts and special characters
    text = (
        text.replace("ä", "ae")
        .replace("ö", "oe")
        .replace("ü", "ue")
        .replace("ß", "ss")
        .replace("Ä", "Ae")
        .replace("Ö", "Oe")
        .replace("Ü", "Ue")
    )
    # Strip gender annotations like (w/m/d), (m/w/d), (d/m/w)
    text = re.sub(r"\([wmd/\s\-]+\)", "", text, flags=re.IGNORECASE)
    # Replace non-alphanumeric with underscores
    text = re.sub(r"[^\w\-]", "_", text)
    text = re.sub(r"_+", "_", text).strip("_")
    return text[:max_len].strip("_")


def get_job_prefix(job_data: Dict[str, Any], fallback_id: int | str = "") -> str:
    """Generate systematic prefix: {jobposition}_{jobID}_{companyname} with safe bounded lengths."""
    role = sanitize_slug(job_data.get("role_title") or "Position", max_len=30)
    jid = sanitize_slug(job_data.get("job_id") or job_data.get("job_id_ref") or fallback_id or "job", max_len=15)
    comp = sanitize_slug(job_data.get("company") or "Company", max_len=25)

    parts = []
    if role:
        parts.append(role)
    if jid and (jid.lower() not in role.lower()):
        parts.append(jid)
    if comp and (comp.lower() not in role.lower()) and (not jid or comp.lower() not in jid.lower()):
        parts.append(comp)

    slug = "_".join(parts)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or f"job_{fallback_id or '1'}"


class Database:
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(__file__).resolve().parent.parent / "career_system.db"
        self.db_path = Path(db_path)
        self.init_db()
        self.sync_profiles_from_filesystem()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self) -> None:
        """Create tables and migrate schema if needed."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            # Profiles table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS profiles (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    default_lang TEXT DEFAULT 'en',
                    data_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Jobs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    priority_order INTEGER DEFAULT 0,
                    company TEXT NOT NULL,
                    role_title TEXT NOT NULL,
                    location TEXT,
                    work_mode TEXT DEFAULT 'On-site',
                    employment_type TEXT DEFAULT 'Full-time',
                    contract_type TEXT DEFAULT 'Permanent / Unbefristet',
                    seniority_level TEXT DEFAULT 'Mid-Level',
                    job_id_ref TEXT,
                    salary_range TEXT,
                    industry_sector TEXT,
                    deadline TEXT,
                    day_posted TEXT,
                    start_date TEXT,
                    contact_person TEXT,
                    contact_email TEXT,
                    contact_phone TEXT,
                    source_file TEXT,
                    source_url TEXT,
                    pdf_path TEXT,
                    folder_path TEXT,
                    status TEXT DEFAULT 'New',
                    extracted_skills_json TEXT,
                    responsibilities_json TEXT,
                    requirements_json TEXT,
                    benefits_json TEXT,
                    metadata_json TEXT,
                    full_text TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Schema migration helper
            columns = [c[1] for c in cursor.execute("PRAGMA table_info(jobs)").fetchall()]
            extra_cols = [
                ("priority_order", "INTEGER DEFAULT 0"),
                ("work_mode", "TEXT DEFAULT 'On-site'"),
                ("employment_type", "TEXT"),
                ("contract_type", "TEXT"),
                ("seniority_level", "TEXT"),
                ("job_id_ref", "TEXT"),
                ("salary_range", "TEXT"),
                ("industry_sector", "TEXT"),
                ("day_posted", "TEXT"),
                ("contact_person", "TEXT"),
                ("contact_email", "TEXT"),
                ("contact_phone", "TEXT"),
                ("pdf_path", "TEXT"),
                ("folder_path", "TEXT"),
                ("responsibilities_json", "TEXT"),
                ("requirements_json", "TEXT"),
                ("benefits_json", "TEXT"),
                ("metadata_json", "TEXT"),
            ]
            for col_name, col_type in extra_cols:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass

            # Contacts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS contacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company TEXT NOT NULL,
                    contact_name TEXT NOT NULL,
                    position TEXT,
                    linkedin_url TEXT,
                    email TEXT,
                    phone TEXT,
                    status TEXT DEFAULT 'Identified',
                    notes TEXT,
                    last_contact TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.commit()

    def sync_profiles_from_filesystem(self) -> None:
        """Scan profiles/ directory and sync into database."""
        profiles_dir = self.db_path.parent / "profiles"
        if not profiles_dir.exists():
            return

        with self.get_connection() as conn:
            for prof_dir in profiles_dir.iterdir():
                if prof_dir.is_dir():
                    prof_id = prof_dir.name
                    prof_file = prof_dir / "profile.yaml"
                    if prof_file.exists():
                        try:
                            with open(prof_file, "r", encoding="utf-8") as f:
                                data = yaml.safe_load(f)
                                if data and "personal" in data:
                                    name = data["personal"].get("full_name", prof_id.capitalize())
                                    conn.execute(
                                        """
                                        INSERT INTO profiles (id, name, default_lang, data_json, updated_at)
                                        VALUES (?, ?, ?, ?, ?)
                                        ON CONFLICT(id) DO UPDATE SET
                                            name = excluded.name,
                                            data_json = excluded.data_json,
                                            updated_at = excluded.updated_at
                                        """,
                                        (prof_id, name, "en", json.dumps(data), datetime.now().isoformat()),
                                    )
                        except Exception:
                            pass
            conn.commit()

    # --- Profile Operations ---
    def get_all_profiles(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT id, name, default_lang, updated_at FROM profiles").fetchall()
            return [dict(r) for r in rows]

    def get_profile(self, profile_id: str) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM profiles WHERE id = ?", (profile_id,)).fetchone()
            if row:
                res = dict(row)
                try:
                    res["data"] = json.loads(res["data_json"])
                except Exception:
                    res["data"] = {}
                return res
        return None

    def save_profile(self, profile_id: str, profile_data: Dict[str, Any]) -> None:
        name = profile_data.get("personal", {}).get("full_name", profile_id.capitalize())
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO profiles (id, name, default_lang, data_json, updated_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    name = excluded.name,
                    data_json = excluded.data_json,
                    updated_at = excluded.updated_at
                """,
                (profile_id, name, "en", json.dumps(profile_data), now),
            )
            conn.commit()

        prof_dir = self.db_path.parent / "profiles" / profile_id
        prof_dir.mkdir(parents=True, exist_ok=True)
        with open(prof_dir / "profile.yaml", "w", encoding="utf-8") as f:
            yaml.safe_dump(profile_data, f, sort_keys=False, allow_unicode=True)

    # --- Job Operations with Priority Order & Local Folder Sync ---
    def add_or_update_job(self, job_data: Dict[str, Any]) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Determine next priority order (top of list)
            max_order_row = cursor.execute("SELECT MIN(priority_order) as min_order FROM jobs").fetchone()
            next_priority = (max_order_row["min_order"] - 1) if (max_order_row and max_order_row["min_order"] is not None) else 0

            skills_json = json.dumps(job_data.get("extracted_skills", []))
            resp_json = json.dumps(job_data.get("key_responsibilities", job_data.get("responsibilities", [])))
            req_json = json.dumps(job_data.get("required_qualifications", job_data.get("requirements", [])))
            ben_json = json.dumps(job_data.get("benefits_perks", job_data.get("benefits", [])))
            
            meta = {
                "key_responsibilities": job_data.get("key_responsibilities", []),
                "required_qualifications": job_data.get("required_qualifications", []),
                "preferred_qualifications": job_data.get("preferred_qualifications", []),
                "tech_stack_tools": job_data.get("tech_stack_tools", []),
                "language_requirements": job_data.get("language_requirements", []),
                "benefits_perks": job_data.get("benefits_perks", []),
                "hiring_manager_contact": job_data.get("contact_person", job_data.get("hiring_manager_contact", "")),
            }
            metadata_json = json.dumps(meta)

            cursor.execute(
                """
                INSERT INTO jobs (
                    priority_order, company, role_title, location, work_mode, employment_type, contract_type,
                    seniority_level, job_id_ref, salary_range, industry_sector,
                    deadline, day_posted, start_date, contact_person, contact_email, contact_phone,
                    source_file, source_url, pdf_path, folder_path,
                    status, extracted_skills_json, responsibilities_json, requirements_json, benefits_json,
                    metadata_json, full_text, created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_data.get("priority_order", next_priority),
                    job_data.get("company", "Target Company"),
                    job_data.get("role_title", "Position"),
                    job_data.get("location", "Location"),
                    job_data.get("work_mode", "On-site"),
                    job_data.get("employment_type", "Full-time"),
                    job_data.get("contract_type", "Permanent / Unbefristet"),
                    job_data.get("seniority_level", "Mid-Level"),
                    job_data.get("job_id_ref", job_data.get("job_id", "")),
                    job_data.get("salary_range", "Not disclosed"),
                    job_data.get("industry_sector", "Technology / Engineering"),
                    job_data.get("deadline", job_data.get("application_deadline", "")),
                    job_data.get("day_posted", ""),
                    job_data.get("start_date", ""),
                    job_data.get("contact_person", job_data.get("hiring_manager_contact", "")),
                    job_data.get("contact_email", ""),
                    job_data.get("contact_phone", ""),
                    job_data.get("source_file", ""),
                    job_data.get("source_url", ""),
                    job_data.get("pdf_path", ""),
                    job_data.get("folder_path", ""),
                    job_data.get("status", "New"),
                    skills_json,
                    resp_json,
                    req_json,
                    ben_json,
                    metadata_json,
                    job_data.get("full_text", ""),
                    now,
                    now,
                ),
            )
            conn.commit()
            job_id = cursor.lastrowid

            # Create dedicated job folder: jobs/{jobposition}_{jobID}_{companyname}
            prefix = get_job_prefix(job_data, job_id)
            folder_name = prefix
            job_folder = self.db_path.parent / "jobs" / folder_name
            try:
                os.makedirs(job_folder, exist_ok=True)
                meta_filename = f"{prefix}_meta_data.json"
                with open(job_folder / meta_filename, "w", encoding="utf-8") as f:
                    json.dump({**job_data, "id": job_id, "prefix": prefix}, f, indent=2, ensure_ascii=False)
            except Exception as err:
                print(f"[Database] Warning creating job metadata file: {err}")

            cursor.execute("UPDATE jobs SET folder_path = ? WHERE id = ?", (f"/jobs/{folder_name}", job_id))
            conn.commit()
            return job_id

    def update_job(self, job_id: int, job_data: Dict[str, Any]) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            skills_json = json.dumps(job_data.get("extracted_skills", []))
            resp_json = json.dumps(job_data.get("key_responsibilities", job_data.get("responsibilities", [])))
            req_json = json.dumps(job_data.get("required_qualifications", job_data.get("requirements", [])))
            ben_json = json.dumps(job_data.get("benefits_perks", job_data.get("benefits", [])))
            
            meta = job_data.get("metadata", {})
            if not meta:
                meta = {
                    "key_responsibilities": job_data.get("key_responsibilities", []),
                    "required_qualifications": job_data.get("required_qualifications", []),
                    "preferred_qualifications": job_data.get("preferred_qualifications", []),
                    "tech_stack_tools": job_data.get("tech_stack_tools", []),
                    "language_requirements": job_data.get("language_requirements", []),
                    "benefits_perks": job_data.get("benefits_perks", []),
                    "hiring_manager_contact": job_data.get("contact_person", job_data.get("hiring_manager_contact", "")),
                }
            metadata_json = json.dumps(meta)

            cursor.execute(
                """
                UPDATE jobs SET
                    company = ?, role_title = ?, location = ?, work_mode = ?, employment_type = ?,
                    contract_type = ?, seniority_level = ?, job_id_ref = ?, salary_range = ?,
                    industry_sector = ?, deadline = ?, day_posted = ?, contact_person = ?,
                    contact_email = ?, contact_phone = ?, status = ?, extracted_skills_json = ?,
                    responsibilities_json = ?, requirements_json = ?, benefits_json = ?,
                    metadata_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    job_data.get("company", "Target Company"),
                    job_data.get("role_title", "Position"),
                    job_data.get("location", "Location"),
                    job_data.get("work_mode", "On-site"),
                    job_data.get("employment_type", "Full-time"),
                    job_data.get("contract_type", "Permanent / Unbefristet"),
                    job_data.get("seniority_level", "Mid-Level"),
                    job_data.get("job_id_ref", job_data.get("job_id", "")),
                    job_data.get("salary_range", "Not disclosed"),
                    job_data.get("industry_sector", "Technology / Engineering"),
                    job_data.get("deadline", job_data.get("application_deadline", "")),
                    job_data.get("day_posted", ""),
                    job_data.get("contact_person", ""),
                    job_data.get("contact_email", ""),
                    job_data.get("contact_phone", ""),
                    job_data.get("status", "New"),
                    skills_json,
                    resp_json,
                    req_json,
                    ben_json,
                    metadata_json,
                    now,
                    job_id,
                ),
            )
            conn.commit()

            # Update meta json in folder
            row = conn.execute("SELECT folder_path FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row and row["folder_path"]:
                folder_path = self.db_path.parent / row["folder_path"].lstrip("/")
                if folder_path.exists():
                    prefix = get_job_prefix(job_data, job_id)
                    meta_filename = f"{prefix}_meta_data.json"
                    with open(folder_path / meta_filename, "w", encoding="utf-8") as f:
                        json.dump({**job_data, "id": job_id, "prefix": prefix}, f, indent=2, ensure_ascii=False)

    def reorder_jobs(self, job_ids: List[int]) -> None:
        """Persist drag-and-drop song-style priority ordering."""
        with self.get_connection() as conn:
            for index, j_id in enumerate(job_ids):
                conn.execute("UPDATE jobs SET priority_order = ? WHERE id = ?", (index, int(j_id)))
            conn.commit()

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        """Retrieve all jobs sorted by priority_order then descending ID."""
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY priority_order ASC, id DESC").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["extracted_skills"] = json.loads(d.get("extracted_skills_json") or "[]")
                d["responsibilities"] = json.loads(d.get("responsibilities_json") or "[]")
                d["requirements"] = json.loads(d.get("requirements_json") or "[]")
                d["benefits"] = json.loads(d.get("benefits_json") or "[]")
                try:
                    d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                except Exception:
                    d["metadata"] = {}
                result.append(d)
            return result

    def get_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        with self.get_connection() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row:
                d = dict(row)
                d["extracted_skills"] = json.loads(d.get("extracted_skills_json") or "[]")
                d["responsibilities"] = json.loads(d.get("responsibilities_json") or "[]")
                d["requirements"] = json.loads(d.get("requirements_json") or "[]")
                d["benefits"] = json.loads(d.get("benefits_json") or "[]")
                try:
                    d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                except Exception:
                    d["metadata"] = {}
                return d
        return None

    def delete_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        job = self.get_job(job_id)
        if not job:
            return None
        with self.get_connection() as conn:
            conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()

        # Delete local folder if exists
        if job.get("folder_path"):
            folder = self.db_path.parent / job["folder_path"].lstrip("/")
            if folder.exists():
                import shutil
                try:
                    shutil.rmtree(folder)
                except Exception:
                    pass
        return job

    def update_job_status(self, job_id: int, status: str) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?", (status, datetime.now().isoformat(), job_id))
            conn.commit()

    # --- Document & Outreach Local Persistence ---
    def save_job_doc(self, job_id: int, doc_type: str, lang: str, html_content: str) -> str:
        """Save edited HTML document directly to the dedicated job folder."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        folder_path = self.db_path.parent / (job.get("folder_path", f"/jobs/job_{job_id}").lstrip("/"))
        folder_path.mkdir(parents=True, exist_ok=True)

        prefix = get_job_prefix(job, job_id)
        doc_filename = f"{prefix}_{doc_type}_{lang.lower()}.html"
        target_file = folder_path / doc_filename

        with open(target_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return str(target_file)

    def get_job_doc(self, job_id: int, doc_type: str, lang: str) -> Optional[str]:
        """Load edited HTML document from the dedicated job folder."""
        job = self.get_job(job_id)
        if not job or not job.get("folder_path"):
            return None
        
        folder_path = self.db_path.parent / job["folder_path"].lstrip("/")
        prefix = get_job_prefix(job, job_id)
        doc_filename = f"{prefix}_{doc_type}_{lang.lower()}.html"
        target_file = folder_path / doc_filename

        if target_file.exists():
            with open(target_file, "r", encoding="utf-8") as f:
                return f.read()
        return None

    def save_job_outreach(self, job_id: int, outreach_data: Dict[str, Any]) -> str:
        """Save customized outreach pitches to the dedicated job folder."""
        job = self.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found")
        
        folder_path = self.db_path.parent / (job.get("folder_path", f"/jobs/job_{job_id}").lstrip("/"))
        folder_path.mkdir(parents=True, exist_ok=True)

        prefix = get_job_prefix(job, job_id)
        json_file = folder_path / f"{prefix}_outreach.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(outreach_data, f, indent=2, ensure_ascii=False)

        return str(json_file)

    def get_job_outreach(self, job_id: int) -> Optional[Dict[str, Any]]:
        """Load outreach pitches from the dedicated job folder."""
        job = self.get_job(job_id)
        if not job or not job.get("folder_path"):
            return None
        
        folder_path = self.db_path.parent / job["folder_path"].lstrip("/")
        prefix = get_job_prefix(job, job_id)
        json_file = folder_path / f"{prefix}_outreach.json"

        if json_file.exists():
            with open(json_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
