"""
Google Workspace Synchronization & Export Helper
Supports Google Drive folder sync, Google Docs generation, and Google Sheets CRM logging.
Includes webhook integration for zero-configuration Google Apps Script automation.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional
import requests


# Ready-to-use Google Apps Script template for users
GOOGLE_APPS_SCRIPT_TEMPLATE = """
/**
 * Career System Google Drive & Sheets Integration Script
 * Paste this in your Google Sheet -> Extensions -> Apps Script -> Deploy as Web App
 */
function doPost(e) {
  try {
    var data = JSON.parse(e.postData.contents);
    var action = data.action;
    
    if (action === "log_job") {
      var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
      sheet.appendRow([
        new Date(),
        data.candidate || "",
        data.company || "",
        data.role || "",
        data.location || "",
        data.deadline || "",
        data.fit_score || "",
        data.status || "Applied",
        data.notes || ""
      ]);
      return ContentService.createTextOutput(JSON.stringify({status: "success", message: "Job logged to Sheet"}));
    }
    
    if (action === "create_doc") {
      var doc = DocumentApp.create(data.title || "Application Document");
      var body = doc.getBody();
      body.setText(data.content || "");
      return ContentService.createTextOutput(JSON.stringify({
        status: "success",
        doc_url: doc.getUrl(),
        doc_id: doc.getId()
      }));
    }
    
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: "Unknown action"}));
  } catch (err) {
    return ContentService.createTextOutput(JSON.stringify({status: "error", message: err.toString()}));
  }
}
"""


class GoogleWorkspaceSync:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = webhook_url or os.getenv("GOOGLE_WEBHOOK_URL")

    def sync_job_to_sheet(self, job_data: Dict[str, Any], candidate_name: str, fit_score: str = "") -> Dict[str, Any]:
        """Send job record to Google Sheet via Webhook if configured."""
        if not self.webhook_url:
            return {"status": "offline", "message": "Google Webhook not configured"}

        payload = {
            "action": "log_job",
            "candidate": candidate_name,
            "company": job_data.get("company", ""),
            "role": job_data.get("role_title", ""),
            "location": job_data.get("location", ""),
            "deadline": job_data.get("deadline", ""),
            "fit_score": fit_score,
            "status": job_data.get("status", "New"),
            "notes": f"Skills: {', '.join(job_data.get('extracted_skills', []))}",
        }
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def create_google_doc(self, title: str, content: str) -> Dict[str, Any]:
        """Create a Google Doc in Drive via Webhook if configured."""
        if not self.webhook_url:
            return {"status": "offline", "message": "Google Webhook not configured"}

        payload = {
            "action": "create_doc",
            "title": title,
            "content": content,
        }
        try:
            res = requests.post(self.webhook_url, json=payload, timeout=10)
            return res.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def format_cv_for_google_docs(self, profile: Dict[str, Any], lang: str = "en") -> str:
        """Format candidate profile as clean, paste-ready text for Google Docs."""
        personal = profile.get("personal", {})
        lines = [
            personal.get("full_name", "").upper(),
            f"{personal.get('title_en', '')} | {personal.get('city_en', '')}",
            f"Email: {personal.get('email', '')} | Phone: {personal.get('phone', '')} | LinkedIn: {personal.get('linkedin_url', '')}",
            "\n" + "=" * 50,
            "EXECUTIVE PROFILE",
            "=" * 50,
            profile.get("executive_summary", {}).get(lang, ""),
            "\n" + "=" * 50,
            "PROFESSIONAL EXPERIENCE",
            "=" * 50,
        ]

        for exp in profile.get("experience", []):
            role = exp.get(f"role_{lang}", exp.get("role_en", ""))
            period = exp.get(f"period_{lang}", exp.get("period_en", ""))
            inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))
            lines.append(f"\n{role} | {period}")
            lines.append(inst)
            for b in exp.get("bullets", []):
                lines.append(f"  • {b}")

        lines.extend([
            "\n" + "=" * 50,
            "EDUCATION",
            "=" * 50,
        ])
        for edu in profile.get("education", []):
            lines.append(f"{edu.get('degree_en', '')} - {edu.get('institution', '')} ({edu.get('period_en', '')})")
            if edu.get("notes_en"):
                lines.append(f"  {edu.get('notes_en')}")

        lang_items = [f"{l.get('language', '')} ({l.get('level', '')})" for l in profile.get("skills", {}).get("languages", [])]
        domains_str = ", ".join(profile.get("skills", {}).get("domains", []))
        tools_str = ", ".join(profile.get("skills", {}).get("software_tools", []))
        langs_str = ", ".join(lang_items)

        lines.extend([
            "\n" + "=" * 50,
            "SKILLS & EXPERTISE",
            "=" * 50,
            f"Core Domains: {domains_str}",
            f"Software & Tools: {tools_str}",
            f"Languages: {langs_str}",
        ])

        return "\n".join(lines)
