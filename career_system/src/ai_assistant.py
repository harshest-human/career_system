"""
AI Assistant and Reasoning Engine for Career System
Synthesizes candidate profile data, job requirements, and applicant 'Why I Fit' notes.
Provides structured Job Description Breakdown via Google Gemini API with smart offline NLP fallback.
"""

from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional


class CareerAIAssistant:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def extract_job_breakdown(self, job_text: str, custom_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Extract deep, structured breakdown from job advertisement text using Gemini API or offline NLP."""
        active_key = custom_api_key or self.api_key
        if active_key:
            try:
                from google import genai
                client = genai.Client(api_key=active_key)
                prompt = f"""
You are an expert ATS recruitment analyst and technical job parser.
Analyze this job description carefully and extract all key metadata and requirement categories into a clean, structured JSON object.

JOB DESCRIPTION TEXT:
\"\"\"
{job_text[:9000]}
\"\"\"

Return ONLY valid JSON adhering to this exact schema:
{{
  "company": "Company Name",
  "role_title": "Position Title",
  "location": "City, Country or Remote / Hybrid",
  "employment_type": "Full-time / Part-time / Internship / Freelance",
  "contract_type": "Permanent / Fixed-term / Unlimited",
  "seniority_level": "Junior / Mid-Level / Senior / Lead / Executive / Entry",
  "job_id": "Job Reference Number or Req ID if present, otherwise ''",
  "salary_range": "Salary or Compensation if mentioned, otherwise 'Not disclosed'",
  "application_deadline": "Deadline date or earliest start date if mentioned, otherwise ''",
  "industry_sector": "Industry or Domain (e.g. Agricultural Tech, Data Analytics, Software, Consulting)",
  "extracted_skills": ["skill1", "skill2", "skill3"],
  "key_responsibilities": [
    "Responsibility item 1",
    "Responsibility item 2",
    "Responsibility item 3"
  ],
  "required_qualifications": [
    "Must-have requirement 1",
    "Must-have requirement 2"
  ],
  "preferred_qualifications": [
    "Nice-to-have qualification 1",
    "Nice-to-have qualification 2"
  ],
  "tech_stack_tools": [
    "Tool/Software/Framework 1",
    "Tool/Software/Framework 2"
  ],
  "language_requirements": [
    "English (Fluent/C1)",
    "German (B2/Professional)"
  ],
  "benefits_perks": [
    "Perk 1 (e.g., 30 days vacation, hybrid work, training budget)"
  ],
  "hiring_manager_contact": "Contact person name, email or department if mentioned"
}}
"""
                for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        text_out = response.text
                        json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
                    except Exception:
                        continue
            except Exception as e:
                print(f"[AI Assistant] Gemini Job Breakdown error: {e}. Falling back to NLP heuristics.")

        # Robust Offline NLP Fallback Parser
        return self._offline_job_breakdown(job_text)

    def _offline_job_breakdown(self, text: str) -> Dict[str, Any]:
        """Rule-based heuristic extractor for offline operation."""
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        company = "Target Company"
        role_title = "Position"
        location = "Hamburg, Germany"

        # Heuristic search for company & role in top 10 lines
        for l in lines[:10]:
            if any(term in l.lower() for term in ["gmbh", "ag", "inc", "corp", "kg", "se", "ltd", "consulting", "institute"]):
                company = l.replace("Willkommen bei", "").strip()
                break

        for l in lines[:12]:
            if any(term in l.lower() for term in ["engineer", "consultant", "analyst", "developer", "manager", "scientist", "spezialist", "wissenschaftlicher"]):
                role_title = l
                break

        # Employment and contract type detection
        lowered = text.lower()
        emp_type = "Full-time"
        if "teilzeit" in lowered or "part-time" in lowered or "part time" in lowered:
            emp_type = "Part-time"
        elif "werkstudent" in lowered or "intern" in lowered or "praktik" in lowered:
            emp_type = "Internship / Working Student"

        contract = "Permanent / Unlimited"
        if "befristet" in lowered or "fixed-term" in lowered or "temporary" in lowered:
            contract = "Fixed-term (Befristet)"

        seniority = "Mid-Level"
        if "senior" in lowered or "lead" in lowered or "principal" in lowered:
            seniority = "Senior"
        elif "junior" in lowered or "entry" in lowered or "einsteiger" in lowered:
            seniority = "Junior"
        elif "phd" in lowered or "promotion" in lowered or "postdoc" in lowered:
            seniority = "Postdoc / PhD Specialist"

        # Extract Job ID
        job_id_match = re.search(r"(?:req|job|ref|kennziffer)[-:\s#]*([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
        job_id = job_id_match.group(1) if job_id_match else ""

        # Extract keywords
        known_tech = [
            "python", " r ", "sql", "git", "docker", "tableau", "power bi", "excel",
            "agricultural engineering", "dairy science", "livestock emissions", "sensor technology",
            "greenfeed", "ftir", "gasmet", "time series", "mixed models", "statistics", "esg", "sustainability"
        ]
        matched_skills = []
        for s in known_tech:
            if s.strip().lower() in lowered:
                matched_skills.append(s.strip())

        # Split responsibilities and qualifications if bullet markers exist
        bullet_lines = [l.lstrip("•-* ").strip() for l in lines if l.startswith(("•", "-", "*")) or (len(l) > 20 and l[0].isdigit() and l[1] in ".)")]

        responsibilities = bullet_lines[:4] if len(bullet_lines) >= 4 else [
            "Lead technical analysis and deliver project milestones.",
            "Collaborate with multidisciplinary engineering and science teams.",
            "Coordinate field campaigns, sensor instrumentation, and reporting.",
        ]
        requirements = bullet_lines[4:8] if len(bullet_lines) >= 8 else [
            "Degree in Agricultural Engineering, Data Science, or related technical domain.",
            "Proficiency in statistical modeling and data evaluation (R, Python, SQL).",
            "Hands-on experience with sensor hardware or environmental measurements.",
        ]

        return {
            "company": company,
            "role_title": role_title,
            "location": location,
            "employment_type": emp_type,
            "contract_type": contract,
            "seniority_level": seniority,
            "job_id": job_id,
            "salary_range": "Not disclosed",
            "application_deadline": "As soon as possible",
            "industry_sector": "Engineering & Technology",
            "extracted_skills": matched_skills if matched_skills else ["python", "data analysis", "sensor technology"],
            "key_responsibilities": responsibilities,
            "required_qualifications": requirements,
            "preferred_qualifications": ["German & English communication skills", "Experience with commercial livestock systems"],
            "tech_stack_tools": [s for s in matched_skills if s in ["python", "r", "sql", "docker", "power bi", "tableau", "excel"]],
            "language_requirements": ["English (Fluent / C1)", "German (Professional / B2)"],
            "benefits_perks": ["30 days annual leave", "Flexible / Hybrid work options", "Continuing education support"],
            "hiring_manager_contact": "HR & Talent Acquisition Team",
        }

    def analyze_fit_notes(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str,
        lang: str = "en",
        custom_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Analyze applicant's fit notes and generate tailored cover letter paragraphs and bullet advice."""
        personal = candidate_profile.get("personal", {})
        cand_name = personal.get("full_name", "Applicant")
        company = job_data.get("company", "the company")
        role = job_data.get("role_title", "the position")
        skills = job_data.get("extracted_skills", [])

        active_key = custom_api_key or self.api_key
        if active_key:
            try:
                from google import genai
                client = genai.Client(api_key=active_key)
                prompt = f"""
You are an expert executive career advisor and ATS resume specialist.
Candidate Name: {cand_name}
Target Company: {company}
Target Role: {role}
Required Job Skills: {', '.join(skills)}
Candidate Profile Summary: {candidate_profile.get('executive_summary', {}).get(lang, '')}
Applicant's Personal Notes on Why They Fit: "{user_notes}"
Language: {lang}

Please produce:
1. A tailored 3-paragraph Cover Letter body articulating their specific strengths and personal motivation for this exact role.
2. 3 powerful resume bullet point suggestions incorporating their fit notes and matching keywords.
3. 2 key recommendations to ace the interview with this hiring team.

Format your response as clean JSON with keys:
"cover_letter_paragraphs" (list of strings),
"suggested_bullets" (list of strings),
"interview_recommendations" (list of strings)
"""
                for model_name in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-2.0-flash"]:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        text_out = response.text
                        json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group(0))
                    except Exception:
                        continue
            except Exception as e:
                print(f"[AI Assistant] Gemini API call note: {e}. Using rule-based synthesis.")

        # Offline Fallback
        domains_list = candidate_profile.get("skills", {}).get("domains", []) or []
        primary_domain_en = domains_list[0] if len(domains_list) > 0 else "applied engineering and technical operations"
        primary_domain_de = domains_list[0] if len(domains_list) > 0 else "angewandte Technik und operative Prozesse"

        if lang == "en":
            paragraphs = [
                f"I am writing to express my enthusiastic application for the {role} position at {company}. With my established background in {primary_domain_en} and proven hands-on execution, I offer a direct match for your team's current operational and innovation objectives.",
                f"Regarding your specific requirements: {user_notes if user_notes else f'My background spans core areas including ' + ', '.join(skills[:4])}. I have consistently demonstrated the ability to bridge complex analytical workflows with reliable execution, delivering measurable impact and streamlined collaboration.",
                f"I am particularly drawn to {company} because of your commitment to excellence and technical innovation. I hold valid work authorization in Germany and am available to start in accordance with your timeline. I look forward to discussing how my experience will support {company}'s continued success.",
            ]
            bullets = [
                f"Spearhead technical deliverables aligning with {company}'s requirements in {skills[0] if skills else 'data and operations'}.",
                f"Streamline cross-functional workflows integrating {skills[1] if len(skills) > 1 else 'analytical systems'} to drive measurable efficiency.",
                f"Collaborate with project stakeholders to deliver high-quality outcomes within target timelines.",
            ]
            recs = [
                f"Highlight your direct experience with {', '.join(skills[:3]) if skills else 'core competencies'} during your introductory call.",
                f"Reference specific projects mentioned in your 'Why I Fit' notes during technical interviews.",
            ]
        else:
            paragraphs = [
                f"mit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}. Mein Profil verbindet fundierte Fachkenntnisse in {primary_domain_de} mit zielgerichteter Praxis.",
                f"Bezugnehmend auf Ihre Anforderungen: {user_notes if user_notes else 'Meine Schwerpunkte liegen in der praktischen Umsetzung und datengestützten Analyse.'} In meinen Projekten habe ich stets gezeigt, wie anspruchsvolle Aufgaben strukturiert und termingerecht gelöst werden.",
                f"Ich freue mich darauf, meine Erfahrung bei {company} einzubringen. Ich verfüge über eine uneingeschränkte Arbeitserlaubnis in Deutschland und freue mich auf ein persönliches Kennenlernen.",
            ]
            bullets = [
                f"Erfolgreiche Leitung technischer Arbeitspakete im Bereich {skills[0] if skills else 'Prozessanalyse'}.",
                f"Entwicklung robuster Mess- und Analysemethoden zur nachhaltigen Effizienzsteigerung.",
            ]
            recs = [
                f"Betonen Sie Ihre Praxiserfahrung in {', '.join(skills[:3]) if skills else 'Schwerpunktthemen'} im Erstgespräch.",
            ]

        return {
            "cover_letter_paragraphs": paragraphs,
            "suggested_bullets": bullets,
            "interview_recommendations": recs,
        }
