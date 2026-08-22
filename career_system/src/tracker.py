"""
Lightweight CRM and Networking Tracker Engine
Manages contacts database, interaction logs, and generates personalized outreach messages.
"""

from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml


class NetworkTracker:
    def __init__(
        self,
        contacts_file: Path = Path("network_tracker/contacts.csv"),
        log_file: Path = Path("network_tracker/outreach_log.yaml"),
        templates_dir: Path = Path("network_tracker/templates"),
        profiles_dir: Path = Path("profiles"),
    ):
        self.contacts_file = contacts_file
        self.log_file = log_file
        self.templates_dir = templates_dir
        self.profiles_dir = profiles_dir

    def load_contacts(self) -> pd.DataFrame:
        """Load contacts CSV."""
        if not self.contacts_file.exists():
            return pd.DataFrame(columns=[
                "Company", "Contact_Name", "Position", "LinkedIn_URL",
                "Email", "Phone", "Requisition_ID", "Candidate_Target",
                "Status", "Last_Contact", "Notes"
            ])
        return pd.read_csv(self.contacts_file)

    def save_contacts(self, df: pd.DataFrame) -> None:
        """Save updated contacts back to CSV."""
        df.to_csv(self.contacts_file, index=False)

    def add_contact(
        self,
        company: str,
        name: str,
        position: str,
        candidate_target: str = "harsh",
        linkedin: str = "",
        email: str = "",
        req_id: str = "",
        status: str = "Identified",
        notes: str = "",
    ) -> None:
        """Add a new contact entry."""
        df = self.load_contacts()
        new_entry = {
            "Company": company,
            "Contact_Name": name,
            "Position": position,
            "LinkedIn_URL": linkedin,
            "Email": email,
            "Phone": "",
            "Requisition_ID": req_id,
            "Candidate_Target": candidate_target,
            "Status": status,
            "Last_Contact": datetime.now().strftime("%Y-%m-%d"),
            "Notes": notes,
        }
        df = pd.concat([df, pd.DataFrame([new_entry])], ignore_index=True)
        self.save_contacts(df)
        print(f"[Tracker] Added contact '{name}' at '{company}'.")

    def generate_pitch(
        self,
        candidate_id: str,
        company: str,
        contact_name: str = "Hiring Team",
        role_title: str = "Open Position",
        template_name: str = "linkedin_connection.txt",
    ) -> str:
        """Render a personalized outreach pitch from a template."""
        # Load profile
        profile_file = self.profiles_dir / candidate_id / "profile.yaml"
        if not profile_file.exists():
            raise FileNotFoundError(f"Profile {candidate_id} not found.")

        with open(profile_file, "r", encoding="utf-8") as f:
            profile = yaml.safe_load(f)

        personal = profile.get("personal", {})
        skills = profile.get("skills", {})
        domains = skills.get("domains", ["Technology & Analytics"])
        hw_tools = skills.get("hardware_instruments", skills.get("software_tools", []))

        replacements = {
            "{{CONTACT_NAME}}": contact_name,
            "{{COMPANY}}": company,
            "{{ROLE_TITLE}}": role_title,
            "{{REQ_ID}}": "REF-2026",
            "{{CANDIDATE_NAME}}": personal.get("full_name", ""),
            "{{CANDIDATE_TITLE}}": personal.get("title_en", ""),
            "{{CANDIDATE_EMAIL}}": personal.get("email", ""),
            "{{CANDIDATE_PHONE}}": personal.get("phone", ""),
            "{{CANDIDATE_LINKEDIN}}": personal.get("linkedin_url", ""),
            "{{INSTITUTION}}": "Leibniz Institute for Agricultural Engineering and Bioeconomy (ATB)",
            "{{CORE_DOMAIN}}": domains[0] if domains else "Innovation & Technology",
            "{{KEY_SKILL_1}}": hw_tools[0] if hw_tools else "Data Analytics",
            "{{KEY_SKILL_2}}": hw_tools[1] if len(hw_tools) > 1 else "Sensor Systems",
            "{{KEY_SKILL_3}}": domains[1] if len(domains) > 1 else "Statistical Modeling",
        }

        tpl_path = self.templates_dir / template_name
        if not tpl_path.exists():
            raise FileNotFoundError(f"Template not found: {tpl_path}")

        with open(tpl_path, "r", encoding="utf-8") as f:
            content = f.read()

        for k, v in replacements.items():
            content = content.replace(k, str(v))

        return content

    def log_interaction(
        self,
        candidate_id: str,
        company: str,
        contact_name: str,
        channel: str,
        message_type: str,
        status: str,
        notes: str,
        next_action_days: int = 7,
    ) -> None:
        """Append an entry to the YAML outreach log."""
        logs = {"outreach_history": []}
        if self.log_file.exists():
            with open(self.log_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "outreach_history" in data:
                    logs = data

        next_date = (pd.Timestamp.now() + pd.Timedelta(days=next_action_days)).strftime("%Y-%m-%d")
        new_log = {
            "id": f"log_{len(logs['outreach_history']) + 1:03d}",
            "timestamp": datetime.now().isoformat(),
            "candidate": candidate_id,
            "company": company,
            "contact_name": contact_name,
            "channel": channel,
            "message_type": message_type,
            "status": status,
            "notes": notes,
            "next_action_date": next_date,
        }
        logs["outreach_history"].append(new_log)

        with open(self.log_file, "w", encoding="utf-8") as f:
            yaml.safe_dump(logs, f, sort_keys=False, allow_unicode=True)

        print(f"[Tracker] Logged interaction for {contact_name} at {company} (Next follow-up: {next_date}).")
