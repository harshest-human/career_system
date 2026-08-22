"""
AI Assistant and Reasoning Engine for Career System
Synthesizes candidate profile data, job requirements, and applicant 'Why I Fit' notes.
Provides structured Job Description Breakdown & End-to-End Master CV Tailoring via Google Gemini API
with intelligent offline NLP fallback.
"""

from __future__ import annotations

import copy
import json
import os
import re
from typing import Any, Dict, List, Optional


class CareerAIAssistant:
    GEMINI_MODELS = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def test_api_key(self, api_key: Optional[str] = None) -> Dict[str, Any]:
        """Test API key connectivity and return active model and status."""
        active_key = api_key or self.api_key
        if not active_key or not active_key.strip():
            return {
                "status": "offline",
                "connected": False,
                "model": "Offline Rule-Based Heuristics",
                "message": "No API key configured. System is running in offline heuristic mode.",
            }

        try:
            from google import genai
            client = genai.Client(api_key=active_key.strip())
            for model_name in self.GEMINI_MODELS:
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents="Respond with the exact word 'READY' if you can read this.",
                    )
                    if response and response.text:
                        return {
                            "status": "connected",
                            "connected": True,
                            "model": model_name,
                            "message": f"Successfully connected to Google Gemini ({model_name}).",
                        }
                except Exception as model_err:
                    continue
            return {
                "status": "error",
                "connected": False,
                "model": "None",
                "message": "API key was provided, but could not connect to Gemini models. Check key validity and quota.",
            }
        except Exception as e:
            return {
                "status": "error",
                "connected": False,
                "model": "None",
                "message": f"Gemini initialization error: {str(e)}",
            }

    def extract_job_breakdown(self, job_text: str, custom_api_key: Optional[str] = None) -> Dict[str, Any]:
        """Extract deep, structured breakdown from job advertisement text using Gemini API or offline NLP."""
        active_key = custom_api_key or self.api_key
        if active_key and active_key.strip():
            try:
                from google import genai
                client = genai.Client(api_key=active_key.strip())
                prompt = f"""
You are an expert ATS recruitment analyst and technical job parser.
Analyze this job description carefully and extract all key metadata and requirement categories into a clean, structured JSON object.

JOB DESCRIPTION TEXT:
\"\"\"
{job_text[:12000]}
\"\"\"

Return ONLY valid JSON adhering to this exact schema:
{{
  "company": "Company Name",
  "role_title": "Position Title",
  "location": "City, Country or Remote / Hybrid",
  "employment_type": "Full-time / Part-time / Ausbildung / Internship / Working Student / Freelance",
  "contract_type": "Permanent / Unlimited / Fixed-term (Befristet) / Temporary",
  "seniority_level": "Junior / Mid-Level / Senior / Lead / Principal / Executive",
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
    "Perk 1 (e.g. 30 days vacation, hybrid work, training budget)"
  ],
  "hiring_manager_contact": "Contact person name, email or department if mentioned"
}}
"""
                for model_name in self.GEMINI_MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        text_out = response.text
                        json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            data["ai_model_used"] = model_name
                            return data
                    except Exception as e:
                        print(f"[AI Assistant] Model {model_name} breakdown error: {e}")
                        continue
            except Exception as e:
                print(f"[AI Assistant] Gemini Job Breakdown error: {e}. Falling back to NLP heuristics.")

        # Robust Offline NLP Fallback Parser
        data = self._offline_job_breakdown(job_text)
        data["ai_model_used"] = "offline_nlp"
        return data

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

    def tailor_application(
        self,
        master_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str = "",
        lang: str = "en",
        custom_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Synthesize Master CV against Job Requirements using Gemini AI.
        Generates:
        1. Tailored Executive Summary (EN & DE)
        2. Tailored Experience list with enhanced/aligned bullets
        3. Tailored Skills matrix matching job keywords
        4. Tailored Cover Letter paragraphs (EN & DE)
        5. Tailored Outreach Pitches (LinkedIn note <300 chars, InMail, Cold Email)
        """
        active_key = custom_api_key or self.api_key
        if active_key and active_key.strip():
            try:
                from google import genai
                client = genai.Client(api_key=active_key.strip())

                prompt = f"""
You are an elite executive career strategist, technical recruiter, and bilingual CV tailoring AI.
Your goal is to tailor the candidate's Master CV, Cover Letter, and Outreach pitches for a specific target job posting.

CANDIDATE MASTER CV DATA:
{json.dumps(master_profile, indent=2, ensure_ascii=False)}

TARGET JOB POSTING DATA:
Company: {job_data.get('company', '')}
Role Title: {job_data.get('role_title', '')}
Location: {job_data.get('location', '')}
Key Responsibilities: {json.dumps(job_data.get('key_responsibilities', []))}
Required Qualifications: {json.dumps(job_data.get('required_qualifications', []))}
Extracted Skills: {json.dumps(job_data.get('extracted_skills', []))}
Tech Stack & Tools: {json.dumps(job_data.get('tech_stack_tools', []))}

APPLICANT'S SPECIFIC 'WHY I FIT' NOTES / HIGHLIGHTS:
\"{user_notes}\"

INSTRUCTIONS:
1. Tailor the Executive Summary in both English (UK) and Deutsch (DE) to immediately position the candidate as a top-tier fit for this company and position.
2. Review the candidate's Master Experience entries. Keep all genuine experience, dates, and institutions intact, but sharpen, enhance, and prioritize the accomplishment bullets to highlight relevant skills, tools, methodologies, and quantified results matching the target job.
3. Organize and prioritize the Skills matrix (domains, software_tools, hardware_instruments, languages) emphasizing the employer's desired stack.
4. Draft a persuasive 3-4 paragraph Cover Letter in English (UK) and Deutsch (DE) directly bridging the candidate's proven experience with the employer's mission and challenges.
5. Create tailored outreach messages:
   - LinkedIn Connection Note (<300 characters strictly)
   - LinkedIn InMail pitch (150-200 words)
   - Tailored Cold Email (subject line + concise body)

Return ONLY valid JSON matching this exact structure:
{{
  "tailored_profile": {{
    "personal": {json.dumps(master_profile.get("personal", {}))},
    "executive_summary": {{
      "en": "Tailored English executive summary...",
      "de": "Maßgeschneiderte deutsche Zusammenfassung..."
    }},
    "experience": [
      {{
        "role_en": "Job Title (EN)",
        "role_de": "Job Title (DE)",
        "institution_en": "Company / Organization",
        "institution_de": "Company / Organization",
        "period_en": "2022 - Present",
        "period_de": "2022 - Heute",
        "affiliation": "Location or department",
        "bullets": [
          "Tailored accomplishment bullet 1 highlighting matching keywords and impact.",
          "Tailored accomplishment bullet 2."
        ]
      }}
    ],
    "education": {json.dumps(master_profile.get("education", []))},
    "skills": {json.dumps(master_profile.get("skills", {}))},
    "leadership_awards": {json.dumps(master_profile.get("leadership_awards", []))}
  }},
  "cover_letter_paragraphs": {{
    "en": [
      "Paragraph 1: Introduction and compelling statement of match...",
      "Paragraph 2: Deep dive into technical achievements and project match...",
      "Paragraph 3: Motivation for this company and work authorization / availability."
    ],
    "de": [
      "Absatz 1: Einleitung und prägnante Begründung der Eignung...",
      "Absatz 2: Vertiefung der fachlichen Erfolge und passenden Projekte...",
      "Absatz 3: Motivation für das Unternehmen und Verfügbarkeit."
    ]
  }},
  "outreach": {{
    "linkedin_connection": "Hi [Name], I noticed your work at [Company] regarding [Topic]. With my background in [Skill], I'd love to connect and share insights on [Topic]. Best, [Candidate]",
    "linkedin_inmail": "Dear [Name], ...",
    "cold_email_subject": "Application: [Role] — [Candidate Full Name]",
    "cold_email_body": "Dear [Name] / Hiring Team,\\n\\n..."
  }},
  "tailoring_highlights": [
    "Emphasized Python and data analysis in recent role",
    "Tailored cover letter to highlight experience with sensor hardware"
  ]
}}
"""
                for model_name in self.GEMINI_MODELS:
                    try:
                        response = client.models.generate_content(
                            model=model_name,
                            contents=prompt,
                        )
                        text_out = response.text
                        json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                        if json_match:
                            data = json.loads(json_match.group(0))
                            data["ai_model_used"] = model_name
                            return data
                    except Exception as e:
                        print(f"[AI Assistant] Model {model_name} tailoring error: {e}")
                        continue
            except Exception as e:
                print(f"[AI Assistant] Gemini tailoring failed: {e}. Using rule-based synthesizer.")

        # Offline Fallback Synthesizer
        return self._offline_tailor_application(master_profile, job_data, user_notes, lang)

    def _offline_tailor_application(
        self,
        master_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str = "",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """High-quality heuristic synthesis when offline."""
        tailored_prof = copy.deepcopy(master_profile)
        company = job_data.get("company") or "Target Company"
        role = job_data.get("role_title") or "the position"
        skills = job_data.get("extracted_skills", [])

        domains_list = master_profile.get("skills", {}).get("domains", []) or []
        primary_domain_en = domains_list[0] if len(domains_list) > 0 else "applied engineering and technical operations"
        primary_domain_de = domains_list[0] if len(domains_list) > 0 else "angewandte Technik und operative Prozesse"

        cand_name = master_profile.get("personal", {}).get("full_name", "Applicant")

        # Synthesize tailored summaries
        tailored_prof["executive_summary"] = {
            "en": f"Results-driven professional with deep expertise in {primary_domain_en} and demonstrated success delivering high-impact solutions. Direct technical alignment with {company}'s {role} objectives.",
            "de": f"Ergebnisorientierter Spezialist mit fundierter Expertise in {primary_domain_de} und nachgewiesenen Erfolgen bei der Umsetzung anspruchsvoller Projekte. Ideale Passung für die Position als {role} bei {company}.",
        }

        # Enhance experience bullets if present
        if tailored_prof.get("experience"):
            for exp in tailored_prof["experience"]:
                if "bullets" not in exp or not exp["bullets"]:
                    exp["bullets"] = [
                        f"Led technical execution aligning with core requirements in {skills[0] if skills else 'engineering and analysis'}.",
                        f"Streamlined cross-functional operations to accelerate project milestones and maintain quality standards.",
                    ]

        # Synthesize bilingual cover letters
        cover_en = [
            f"I am writing to express my enthusiastic application for the {role} position at {company}. With my background in {primary_domain_en} and proven hands-on execution, I offer a direct match for your team's current operational and innovation objectives.",
            f"Regarding your specific requirements: {user_notes if user_notes else ('My background spans core areas including ' + ', '.join(skills[:4]) if skills else 'I have consistently bridged complex analytical workflows with reliable execution.')}. I have delivered measurable impact and streamlined collaboration across technical teams.",
            f"I am particularly drawn to {company} because of your commitment to technical innovation and excellence. I hold valid work authorization in Germany and look forward to discussing how my experience will support {company}'s continued success.",
        ]

        cover_de = [
            f"mit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}. Mein Profil verbindet fundierte Fachkenntnisse in {primary_domain_de} mit zielgerichteter Praxis.",
            f"Bezugnehmend auf Ihre Anforderungen: {user_notes if user_notes else 'Meine Schwerpunkte liegen in der praktischen Umsetzung und datengestützten Analyse.'} In meinen Projekten habe ich stets gezeigt, wie anspruchsvolle Aufgaben strukturiert und termingerecht gelöst werden.",
            f"Ich freue mich darauf, meine Erfahrung bei {company} einzubringen. Ich verfüge über eine uneingeschränkte Arbeitserlaubnis in Deutschland und freue mich auf ein persönliches Kennenlernen.",
        ]

        # Synthesize outreach
        outreach = {
            "linkedin_connection": f"Hi {job_data.get('hiring_manager_contact', 'there')}, I saw your opening for {role} at {company}. My background in {primary_domain_en} aligns closely. Would love to connect!",
            "linkedin_inmail": f"Hi {job_data.get('hiring_manager_contact', 'Hiring Team')},\n\nI recently came across the {role} opportunity at {company}. Given my background in {primary_domain_en} and experience with {', '.join(skills[:3]) if skills else 'technical solutions'}, I wanted to reach out directly. I'd welcome the chance to briefly discuss how my background aligns with your team's goals.\n\nBest regards,\n{cand_name}",
            "cold_email_subject": f"Application: {role} — {cand_name}",
            "cold_email_body": f"Dear {job_data.get('hiring_manager_contact', 'Hiring Team')},\n\nI am writing to express my strong interest in the {role} role at {company}.\n\nWith extensive experience in {primary_domain_en} and hands-on proficiency in {', '.join(skills[:3]) if skills else 'core competencies'}, I have consistently delivered measurable outcomes.\n\nPlease find my tailored CV attached for your review. I would welcome the opportunity to discuss my qualifications.\n\nSincerely,\n{cand_name}",
        }

        return {
            "tailored_profile": tailored_prof,
            "cover_letter_paragraphs": {
                "en": cover_en,
                "de": cover_de,
            },
            "outreach": outreach,
            "tailoring_highlights": [
                f"Generated tailored summaries for {company}",
                "Structured cover letter and outreach pitches",
            ],
            "ai_model_used": "offline_nlp",
        }

    def analyze_fit_notes(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str,
        lang: str = "en",
        custom_api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Backwards-compatible wrapper that delegates to tailor_application."""
        res = self.tailor_application(
            master_profile=candidate_profile,
            job_data=job_data,
            user_notes=user_notes,
            lang=lang,
            custom_api_key=custom_api_key,
        )
        # Format for legacy callers
        paragraphs = res.get("cover_letter_paragraphs", {}).get(lang) or res.get("cover_letter_paragraphs", {}).get("en", [])
        return {
            "cover_letter_paragraphs": paragraphs,
            "suggested_bullets": [
                b for exp in res.get("tailored_profile", {}).get("experience", []) for b in exp.get("bullets", [])
            ][:3] or [
                f"Spearhead technical deliverables aligning with {job_data.get('company', 'target company')}'s requirements.",
                "Streamline cross-functional workflows to drive measurable efficiency.",
            ],
            "interview_recommendations": [
                f"Highlight direct experience with {', '.join(job_data.get('extracted_skills', [])[:3]) or 'core competencies'} during your introductory call.",
                "Reference specific projects mentioned in your fit notes during technical interviews.",
            ],
            "tailored_profile": res.get("tailored_profile"),
            "outreach": res.get("outreach"),
        }
