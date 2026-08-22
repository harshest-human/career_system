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


def get_job_prefix(job_data: Dict[str, Any], fallback_id: int | str = "") -> str:
    """Generate systematic prefix: {jobposition}_{jobID}_{companyname}."""
    role = re.sub(r"[^\w\-]", "_", str(job_data.get("role_title") or "Position"))
    jid = re.sub(r"[^\w\-]", "_", str(job_data.get("job_id") or job_data.get("job_id_ref") or fallback_id or "job"))
    comp = re.sub(r"[^\w\-]", "_", str(job_data.get("company") or "Company"))

    slug = f"{role}_{jid}_{comp}"
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or f"job_{fallback_id}"


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
                    company TEXT NOT NULL,
                    role_title TEXT NOT NULL,
                    location TEXT,
                    employment_type TEXT,
                    contract_type TEXT,
                    seniority_level TEXT,
                    job_id_ref TEXT,
                    salary_range TEXT,
                    industry_sector TEXT,
                    deadline TEXT,
                    start_date TEXT,
                    source_file TEXT,
                    source_url TEXT,
                    pdf_path TEXT,
                    folder_path TEXT,
                    status TEXT DEFAULT 'New',
                    extracted_skills_json TEXT,
                    metadata_json TEXT,
                    full_text TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
            """)
            # Schema migration helper
            columns = [c[1] for c in cursor.execute("PRAGMA table_info(jobs)").fetchall()]
            extra_cols = [
                ("employment_type", "TEXT"),
                ("contract_type", "TEXT"),
                ("seniority_level", "TEXT"),
                ("job_id_ref", "TEXT"),
                ("salary_range", "TEXT"),
                ("industry_sector", "TEXT"),
                ("pdf_path", "TEXT"),
                ("folder_path", "TEXT"),
                ("metadata_json", "TEXT"),
            ]
            for col_name, col_type in extra_cols:
                if col_name not in columns:
                    try:
                        cursor.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                    except Exception:
                        pass

            # Portal Credentials table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS portal_credentials (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    portal_name TEXT NOT NULL,
                    portal_url TEXT NOT NULL,
                    username TEXT NOT NULL,
                    password TEXT NOT NULL,
                    enabled INTEGER DEFAULT 1,
                    updated_at TEXT NOT NULL
                )
            """)

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
            # Outreach log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS outreach_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    candidate_id TEXT NOT NULL,
                    company TEXT NOT NULL,
                    contact_name TEXT NOT NULL,
                    channel TEXT,
                    message_type TEXT,
                    status TEXT,
                    content TEXT,
                    next_action_date TEXT,
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
                res["data"] = json.loads(res["data_json"])
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

    # --- Portal Credentials Operations ---
    def get_all_portals(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM portal_credentials ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def add_or_update_portal(self, portal_data: Dict[str, Any]) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            portal_id = portal_data.get("id")
            if portal_id:
                cursor.execute(
                    """
                    UPDATE portal_credentials SET
                        portal_name = ?, portal_url = ?, username = ?, password = ?, enabled = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        portal_data.get("portal_name", "Portal"),
                        portal_data.get("portal_url", ""),
                        portal_data.get("username", ""),
                        portal_data.get("password", ""),
                        portal_data.get("enabled", 1),
                        now,
                        portal_id,
                    ),
                )
                conn.commit()
                return portal_id
            else:
                cursor.execute(
                    """
                    INSERT INTO portal_credentials (portal_name, portal_url, username, password, enabled, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        portal_data.get("portal_name", "Portal"),
                        portal_data.get("portal_url", ""),
                        portal_data.get("username", ""),
                        portal_data.get("password", ""),
                        portal_data.get("enabled", 1),
                        now,
                    ),
                )
                conn.commit()
                return cursor.lastrowid

    def delete_portal(self, portal_id: int) -> None:
        with self.get_connection() as conn:
            conn.execute("DELETE FROM portal_credentials WHERE id = ?", (portal_id,))
            conn.commit()

    # --- Job Operations with Systematic Nomenclature ---
    def add_or_update_job(self, job_data: Dict[str, Any]) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            skills_json = json.dumps(job_data.get("extracted_skills", []))
            
            meta = {
                "key_responsibilities": job_data.get("key_responsibilities", []),
                "required_qualifications": job_data.get("required_qualifications", []),
                "preferred_qualifications": job_data.get("preferred_qualifications", []),
                "tech_stack_tools": job_data.get("tech_stack_tools", []),
                "language_requirements": job_data.get("language_requirements", []),
                "benefits_perks": job_data.get("benefits_perks", []),
                "hiring_manager_contact": job_data.get("hiring_manager_contact", ""),
            }
            metadata_json = json.dumps(meta)

            cursor.execute(
                """
                INSERT INTO jobs (company, role_title, location, employment_type, contract_type,
                                  seniority_level, job_id_ref, salary_range, industry_sector,
                                  deadline, start_date, source_file, source_url, pdf_path, folder_path,
                                  status, extracted_skills_json, metadata_json, full_text, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_data.get("company", "Target Company"),
                    job_data.get("role_title", "Position"),
                    job_data.get("location", "Location"),
                    job_data.get("employment_type", "Full-time"),
                    job_data.get("contract_type", "Permanent / Unbefristet"),
                    job_data.get("seniority_level", "Mid-Level"),
                    job_data.get("job_id", job_data.get("job_id_ref", "")),
                    job_data.get("salary_range", "Not disclosed"),
                    job_data.get("industry_sector", "Technology / Engineering"),
                    job_data.get("application_deadline", job_data.get("deadline", "")),
                    job_data.get("start_date", ""),
                    job_data.get("source_file", ""),
                    job_data.get("source_url", ""),
                    job_data.get("pdf_path", ""),
                    job_data.get("folder_path", ""),
                    job_data.get("status", "New"),
                    skills_json,
                    metadata_json,
                    job_data.get("full_text", ""),
                    now,
                    now,
                ),
            )
            conn.commit()
            job_id = cursor.lastrowid

            # Create dedicated job folder following: {jobposition}_{jobID}_{companyname}
            prefix = get_job_prefix(job_data, job_id)
            folder_name = prefix
            job_folder = self.db_path.parent / "jobs" / folder_name
            job_folder.mkdir(parents=True, exist_ok=True)

            # Save initial {jobposition}_{jobID}_{companyname}_meta_data.json
            meta_filename = f"{prefix}_meta_data.json"
            with open(job_folder / meta_filename, "w", encoding="utf-8") as f:
                json.dump({**job_data, "id": job_id}, f, indent=2, ensure_ascii=False)

            cursor.execute("UPDATE jobs SET folder_path = ? WHERE id = ?", (f"/jobs/{folder_name}", job_id))
            conn.commit()
            return job_id

    def update_job(self, job_id: int, job_data: Dict[str, Any]) -> None:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            skills_json = json.dumps(job_data.get("extracted_skills", []))
            
            meta = job_data.get("metadata", {})
            if not meta:
                meta = {
                    "key_responsibilities": job_data.get("key_responsibilities", []),
                    "required_qualifications": job_data.get("required_qualifications", []),
                    "preferred_qualifications": job_data.get("preferred_qualifications", []),
                    "tech_stack_tools": job_data.get("tech_stack_tools", []),
                    "language_requirements": job_data.get("language_requirements", []),
                    "benefits_perks": job_data.get("benefits_perks", []),
                    "hiring_manager_contact": job_data.get("hiring_manager_contact", ""),
                }
            metadata_json = json.dumps(meta)

            cursor.execute(
                """
                UPDATE jobs SET
                    company = ?, role_title = ?, location = ?, employment_type = ?,
                    contract_type = ?, seniority_level = ?, job_id_ref = ?, salary_range = ?,
                    industry_sector = ?, deadline = ?, status = ?, extracted_skills_json = ?,
                    metadata_json = ?, updated_at = ?
                WHERE id = ?
                """,
                (
                    job_data.get("company", "Target Company"),
                    job_data.get("role_title", "Position"),
                    job_data.get("location", "Location"),
                    job_data.get("employment_type", "Full-time"),
                    job_data.get("contract_type", "Permanent / Unbefristet"),
                    job_data.get("seniority_level", "Mid-Level"),
                    job_data.get("job_id_ref", job_data.get("job_id", "")),
                    job_data.get("salary_range", "Not disclosed"),
                    job_data.get("industry_sector", "Technology / Engineering"),
                    job_data.get("deadline", job_data.get("application_deadline", "")),
                    job_data.get("status", "New"),
                    skills_json,
                    metadata_json,
                    now,
                    job_id,
                ),
            )
            conn.commit()

            # Update {jobposition}_{jobID}_{companyname}_meta_data.json in folder if exists
            row = conn.execute("SELECT folder_path FROM jobs WHERE id = ?", (job_id,)).fetchone()
            if row and row["folder_path"]:
                folder_path = self.db_path.parent / row["folder_path"].lstrip("/")
                if folder_path.exists():
                    prefix = get_job_prefix(job_data, job_id)
                    meta_filename = f"{prefix}_meta_data.json"
                    with open(folder_path / meta_filename, "w", encoding="utf-8") as f:
                        json.dump({**job_data, "id": job_id}, f, indent=2, ensure_ascii=False)

    def delete_job(self, job_id: int) -> Optional[Dict[str, Any]]:
        job = self.get_job(job_id)
        if not job:
            return None
        with self.get_connection() as conn:
            conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
            conn.commit()
        return job

    def get_all_jobs(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["extracted_skills"] = json.loads(d["extracted_skills_json"] or "[]")
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
                d["extracted_skills"] = json.loads(d["extracted_skills_json"] or "[]")
                try:
                    d["metadata"] = json.loads(d.get("metadata_json") or "{}")
                except Exception:
                    d["metadata"] = {}
                return d
        return None

    def update_job_status(self, job_id: int, status: str) -> None:
        with self.get_connection() as conn:
            conn.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?", (status, datetime.now().isoformat(), job_id))
            conn.commit()

    # --- Contact Operations ---
    def get_all_contacts(self) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            rows = conn.execute("SELECT * FROM contacts ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]

    def add_contact(self, contact_data: Dict[str, Any]) -> int:
        now = datetime.now().isoformat()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO contacts (company, contact_name, position, linkedin_url, email, phone, status, notes, last_contact, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    contact_data.get("company", ""),
                    contact_data.get("contact_name", "Hiring Contact"),
                    contact_data.get("position", ""),
                    contact_data.get("linkedin_url", ""),
                    contact_data.get("email", ""),
                    contact_data.get("phone", ""),
                    contact_data.get("status", "Identified"),
                    contact_data.get("notes", ""),
                    contact_data.get("last_contact", ""),
                    now,
                ),
            )
            conn.commit()
            return cursor.lastrowid
