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

        # Check explicit Title: and Company: lines
        for l in lines:
            if l.startswith("Title:") and len(l.split("Title:", 1)[1].strip()) > 2:
                role_title = l.split("Title:", 1)[1].strip()
            elif l.startswith("Company:") and len(l.split("Company:", 1)[1].strip()) > 1:
                company = l.split("Company:", 1)[1].strip()

        # Clean title if it contains delimiter
        if "|" in role_title:
            role_title = role_title.split("|")[0].strip()

        # Fallback company detection
        if company == "Target Company":
            for l in lines[:10]:
                if any(term in l.lower() for term in ["gmbh", "ag", "inc", "corp", "kg", "se", "ltd", "consulting", "institute"]):
                    company = l.replace("Willkommen bei", "").replace("Jobs bei", "").strip()
                    break

        if role_title == "Position":
            for l in lines[:15]:
                if any(term in l.lower() for term in ["leiter", "head of", "director", "manager", "scientist", "engineer", "technologist", "entwickler", "consultant", "analyst", "spezialist"]):
                    if len(l) < 80:
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
        if "leiter" in lowered or "head of" in lowered or "director" in lowered:
            seniority = "Head of Department / Lead"
        elif "senior" in lowered or "lead" in lowered or "principal" in lowered:
            seniority = "Senior"
        elif "junior" in lowered or "entry" in lowered or "einsteiger" in lowered:
            seniority = "Junior"
        elif "phd" in lowered or "promotion" in lowered or "postdoc" in lowered:
            seniority = "Postdoc / PhD Specialist"

        # Extract Job ID
        job_id_match = re.search(r"(?:req|job|ref|kennziffer)[-:\s#]*([a-zA-Z0-9_\-]+)", text, re.IGNORECASE)
        job_id = job_id_match.group(1) if job_id_match else ""

        # Broad multi-domain keyword dictionary
        known_tech = [
            "lebensmitteltechnologie", "produktentwicklung", "rezepturentwicklung", "supplements",
            "nahrungsergänzungsmittel", "nutraceuticals", "functional ingredients", "sensory analysis",
            "sensorik", "stage-gate", "quality assurance", "qualitätsmanagement", "haccp", "gmp", "ifs",
            "python", " r ", "sql", "git", "docker", "tableau", "power bi", "excel", "salesforce", "devex",
            "project management", "projektmanagement", "regulatory affairs", "food safety", "lebensmittelsicherheit"
        ]
        matched_skills = []
        for s in known_tech:
            if s.strip().lower() in lowered:
                matched_skills.append(s.strip().title())

        # Section-based Extraction (Deine Mission / Was du mitbringst / Tasks / Requirements)
        responsibilities = []
        requirements = []
        perks = []

        current_sec = None
        for l in lines:
            lower_l = l.lower()
            if any(k in lower_l for k in ["deine mission", "aufgaben", "responsibilities", "ihre aufgaben", "das machst du"]):
                current_sec = "resp"
                continue
            elif any(k in lower_l for k in ["was du mitbringst", "qualifikationen", "requirements", "profil", "das bringst du mit"]):
                current_sec = "req"
                continue
            elif any(k in lower_l for k in ["was wir dir bieten", "benefits", "wir bieten", "perks", "unser angebot"]):
                current_sec = "perks"
                continue
            elif l.startswith("SECTION:") or any(k in lower_l for k in ["über uns", "about us", "dein kontakt"]):
                current_sec = None
                continue

            if current_sec and (l.startswith(("•", "-", "*")) or len(l) > 15):
                cleaned_line = l.lstrip("•-* ").strip()
                if len(cleaned_line) > 10:
                    if current_sec == "resp" and len(responsibilities) < 8:
                        responsibilities.append(cleaned_line)
                    elif current_sec == "req" and len(requirements) < 8:
                        requirements.append(cleaned_line)
                    elif current_sec == "perks" and len(perks) < 6:
                        perks.append(cleaned_line)

        if not responsibilities:
            responsibilities = [
                "Entwicklung und Umsetzung der Produktstrategie und Markteinführung innovativer Produkte.",
                "Steuerung von R&D-Projekten von der Konzeptionierung bis zum erfolgreichen Markteintritt.",
                "Fachliche Koordination von Rezepturoptimierung, sensorischer Evaluierung und Qualitätsstandards."
            ]
        if not requirements:
            requirements = [
                "Abgeschlossenes Studium in Lebensmitteltechnologie, Food Science oder vergleichbare Qualifikation.",
                "Fundierte Praxiserfahrung in Produktentwicklung, Formulierung und Projektmanagement.",
                "Ausgeprägte Team- und Kommunikationskompetenz in Deutsch und Englisch."
            ]
        if not perks:
            perks = [
                "Flexible Arbeitszeiten und Homeoffice-Optionen (New Work)",
                "Attraktive Mitarbeiterrabatte und Sport-/Fitnessförderung",
                "Dynamisches, wachstumsorientiertes Teamumfeld"
            ]

        sector = "Food & Sports Nutrition" if any(w in lowered for w in ["food", "lebensmittel", "supplement", "nutrition", "fitness"]) else "Engineering & Technology"

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
            "industry_sector": sector,
            "extracted_skills": matched_skills if matched_skills else ["Produktentwicklung", "Lebensmitteltechnologie", "Projektmanagement"],
            "key_responsibilities": responsibilities,
            "required_qualifications": requirements,
            "preferred_qualifications": ["German & English communication skills", "Experience with functional foods, supplements or fast-moving formulations"],
            "tech_stack_tools": [s for s in matched_skills if s.lower() in ["python", "r", "sql", "docker", "power bi", "tableau", "excel", "salesforce", "devex"]],
            "language_requirements": ["German (Fluent / Professional)", "English (Fluent / Professional)"],
            "benefits_perks": perks,
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

        personal = master_profile.get("personal", {})
        cand_name = personal.get("full_name", "Applicant")
        cand_title_en = personal.get("title_en", "Technical Application Scientist")
        cand_title_de = personal.get("title_de", "Applikationswissenschaftlerin")

        domains_list = master_profile.get("skills", {}).get("domains", []) or []
        primary_domain_en = (
            domains_list[0] if len(domains_list) > 0 else "Food Technology & Formulation"
        )
        primary_domain_de = (
            "Lebensmitteltechnologie & Produktentwicklung"
            if "food" in primary_domain_en.lower() or "application" in primary_domain_en.lower()
            else primary_domain_en
        )

        # Synthesize tailored summaries
        tailored_prof["executive_summary"] = {
            "en": f"Results-oriented {cand_title_en} with comprehensive expertise in {primary_domain_en}, formulation design, sensory optimization, and technical project delivery. Highly aligned with {company}'s requirements for the {role} position.",
            "de": f"Ergebnisorientierte {cand_title_de} mit fundierter Expertise in {primary_domain_de}, Rezepturoptimierung und sensorischer Evaluierung sowie nachgewiesenen Erfolgen im Projektmanagement. Ideale fachliche und persönliche Passung für die Position als {role} bei {company}.",
        }

        # Enhance experience bullets to highlight relevance
        if tailored_prof.get("experience"):
            for exp in tailored_prof["experience"]:
                if "bullets" not in exp or not exp["bullets"]:
                    exp["bullets"] = [
                        f"Led technical deliverables aligning with core requirements in {skills[0] if skills else 'formulation and product development'}.",
                        "Streamlined cross-functional operations to accelerate project milestones and maintain high quality standards.",
                    ]

        # Synthesize bilingual cover letters
        cover_en = [
            f"I am writing to express my enthusiastic application for the {role} position at {company}. With my background in {primary_domain_en} and my proven track record translating formulation concepts and technical solutions into market-ready products, I offer a direct match for your team's innovation and development goals.",
            f"In my current and previous roles—including as Application Scientist EMENA at Sensient Technologies Europe GmbH—I have served as the key technical bridge between R&D, cross-functional teams, and international clients across food, functional ingredients, and nutraceutical applications. {user_notes if user_notes else 'My background combines hands-on formulation design, sensory analysis, and structured stage-gate project execution with a strong focus on quality and commercial viability.'}",
            f"I am particularly drawn to {company} because of your strong market presence, commitment to quality, and forward-looking product portfolio. Based in Hamburg and holding full work authorization, I look forward to contributing my expertise to {company}'s continued growth and product excellence.",
        ]

        cover_de = [
            f"mit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}. Als erfahrene Spezialistin für {primary_domain_de} und Produktentwicklung verbinde ich fundiertes wissenschaftliches Know-how mit zielgerichteter Praxiserfahrung in der Umsetzung innovativer Rezepturen.",
            f"In meiner bisherigen Tätigkeit als Application Scientist EMENA bei Sensient Technologies Europe GmbH steuere ich die Schnittstelle zwischen R&D, Vertrieb und internationalen Kunden in den Bereichen Lebensmittel, funktionelle Inhaltsstoffe und Nutrazeutika. {user_notes if user_notes else 'Meine Kernkompetenzen liegen in der Entwicklung und Optimierung von Formulierungen, der sensorischen Evaluierung sowie im strukturierten Projektmanagement.'} Ich zeichne mich durch Pragmatismus, Umsetzungsstärke und interdisziplinäre Teamarbeit aus.",
            f"Die Innovationskraft und der hohe Qualitätsanspruch von {company} begeistern mich sehr. Mit Wohnsitz in Hamburg und uneingeschränkter Arbeitserlaubnis freue ich mich auf die Gelegenheit, meine Expertise gewinnbringend in Ihr Team einzubringen und die Produktstrategie erfolgreich mitzugestalten.",
        ]

        # Synthesize outreach
        outreach = {
            "linkedin_connection": f"Hi {job_data.get('hiring_manager_contact', 'there')}, I saw your opening for {role} at {company}. With my background in food tech & functional formulation, I'd love to connect!",
            "linkedin_inmail": f"Dear {job_data.get('hiring_manager_contact', 'Hiring Team')},\n\nI recently came across the {role} opportunity at {company} in Hamburg. Given my background as an Application Scientist in food and nutraceutical formulation (EIT Food M.Sc. & Sensient Technologies), I wanted to reach out directly. I would welcome the opportunity to discuss how my formulation and project management experience align with your team's product goals.\n\nBest regards,\n{cand_name}",
            "cold_email_subject": f"Bewerbung: {role} — {cand_name}",
            "cold_email_body": f"Sehr geehrte Damen und Herren,\n\nmit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}.\n\nAls Application Scientist und Lebensmitteltechnologin mit Schwerpunkt auf funktionellen Inhaltsstoffen und Produktentwicklung bringe ich mehrjährige Erfahrung in Rezepturoptimierung, sensorischer Analyse und Projektsteuerung mit.\n\nGerne stelle ich Ihnen meine Qualifikationen in einem persönlichen Gespräch näher vor. Meine vollständigen Bewerbungsunterlagen finden Sie anbei.\n\nMit freundlichen Grüßen\n{cand_name}",
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
                f"Aligned experience and skills with {role}",
                "Structured bilingual cover letter and outreach pitches",
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
