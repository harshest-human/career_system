"""
Job Advertisement Metadata Extractor
Parses PDF files and text using pdfplumber and regex/NLP heuristics
to systematically extract structured fields (Company, Role, Job ID, Type, Deadline, Responsibilities, Requirements, Skills, Contact, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber
import pypdf


class JobExtractor:
    def __init__(self):
        # Comprehensive bilingual dictionary of domains, instrumentation, software, and methods
        self.known_skills = [
            # Agricultural / Bioeconomy / Livestock / Sensors
            "dairy science", "agricultural engineering", "livestock", "ruminant",
            "methane", "ammonia", "nitrous oxide", "co2", "greenhouse gas", "ghg emissions",
            "greenfeed", "gasmet", "ftir", "crds", "tdlas", "pas", "gc-ms",
            "ndir", "gas sensor", "sensor technology", "sensorik", "messtechnik",
            "barn climate", "stallklima", "ventilation", "lueftung",
            "precision livestock farming", "plf", "animal welfare", "tierwohl", "herd management",
            "esg", "sustainability", "nachhaltigkeit", "carbon footprint", "environmental consulting",
            "milchviehhaltung", "nutztier", "agrartechnik", "emissionsmessung", "versuchsplanung",
            # Data, Analytics & Software
            "python", " r ", "r studio", "matlab", "sql", "git", "latex", "xelatex",
            "tableau", "power bi", "excel", "docker", "machine learning", "deep learning",
            "statistics", "datenanalyse", "data analysis", "data science", "time series",
            "mixed models", "glmm", "regression", "biostatistics",
            # Management & Engineering
            "project management", "projektmanagement", "scrum", "agile", "stakeholder management",
            "technical writing", "field trials", "quality assurance", "troubleshooting",
            "automation", "iot", "lorawan", "rest api", "backend", "system integration"
        ]

    def extract_text_from_pdf(self, pdf_path: Path) -> str:
        """Extract all text from a PDF file using pdfplumber with pypdf fallback."""
        text_chunks = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_chunks.append(extracted)
        except Exception:
            try:
                reader = pypdf.PdfReader(str(pdf_path))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_chunks.append(extracted)
            except Exception as e2:
                print(f"[Extractor] Error reading {pdf_path}: {e2}")

        return "\n".join(text_chunks)

    def extract_sections(self, text: str) -> Dict[str, List[str]]:
        """Extract bulleted or structured sections (Responsibilities, Requirements, Benefits)."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        
        responsibilities = []
        requirements = []
        benefits = []
        
        current_section = None
        
        resp_headers = [
            r"ihre aufgaben", r"deine aufgaben", r"das erwartet sie", r"das erwartet dich",
            r"tasks", r"responsibilities", r"key responsibilities", r"what you will do",
            r"aufgabenbereich", r"taetigkeiten", r"tätigkeiten"
        ]
        req_headers = [
            r"ihr profil", r"dein profil", r"das bringen sie mit", r"das bringst du mit",
            r"requirements", r"qualifications", r"what you bring", r"anforderungsprofil",
            r"ihre qualifikationen", r"voraussetzungen", r"must-haves"
        ]
        ben_headers = [
            r"wir bieten", r"das bieten wir", r"benefits", r"what we offer", r"ihre vorteile",
            r"unsere leistungen", r"perks"
        ]

        bullet_pattern = re.compile(r"^[\u2022\u2023\u25E6\u2043\u2219\*\-\+]\s*(.+)$|^\d+[\.\)]\s*(.+)$")

        for line in lines:
            lower = line.lower().strip(" :-\t")
            
            # Check section header
            if any(re.search(r"\b" + h + r"\b", lower) for h in resp_headers):
                current_section = "resp"
                continue
            elif any(re.search(r"\b" + h + r"\b", lower) for h in req_headers):
                current_section = "req"
                continue
            elif any(re.search(r"\b" + h + r"\b", lower) for h in ben_headers):
                current_section = "ben"
                continue
            elif len(line) > 50 and (":" in line or line.isupper()):
                # Potential new unknown header
                if any(k in lower for k in ["kontakt", "contact", "über uns", "about us"]):
                    current_section = None

            # Extract bullet items under active section
            if current_section:
                match = bullet_pattern.match(line)
                item = match.group(1) or match.group(2) if match else line
                item = item.strip()
                if len(item) > 10 and not any(h in item.lower() for h in resp_headers + req_headers + ben_headers):
                    if current_section == "resp" and len(responsibilities) < 10:
                        responsibilities.append(item)
                    elif current_section == "req" and len(requirements) < 10:
                        requirements.append(item)
                    elif current_section == "ben" and len(benefits) < 10:
                        benefits.append(item)

        return {
            "responsibilities": responsibilities,
            "requirements": requirements,
            "benefits": benefits,
        }

    def parse_job_text(self, text: str, source_filename: str = "") -> Dict[str, Any]:
        """Systematically extract structured fields from raw job text."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_few_lines = "\n".join(lines[:20])

        # 1. Role Title
        role_title = "Position"
        title_patterns = [
            r"(?:Wir suchen(?:\s+ab\s+sofort)?(?:\s+einen|\s+eine)?)\s+([A-Za-z0-9\s&./\-\(\)]+?)(?:\s+(?:bei|at|in|für)\s+|\s*\.|\s*$)",
            r"(?:Position|Job Title|Stellenbezeichnung|Rolle):\s*([A-Za-z0-9\s&./\-\(\)]+)",
            r"((?:Senior\s+|Junior\s+|Lead\s+)?(?:Field Application Specialist|Data Analyst|Data Scientist|Agricultural Engineer|Consultant|Scientist|Project Manager|Software Engineer|Product Manager|Entwickler|Berater|Ingenieur|Projektleiter|Wissenschaftlicher Mitarbeiter|Projektmanager)[A-Za-z0-9\s&./\-\(\)]*)",
        ]
        for pattern in title_patterns:
            match = re.search(pattern, first_few_lines, re.IGNORECASE)
            if match:
                cand = match.group(1).strip(" ,.-:\n\t")
                if len(cand) > 3 and len(cand) < 65 and not cand.lower().startswith("wir suchen"):
                    role_title = cand
                    break

        if role_title == "Position" and "_" in source_filename:
            parts = source_filename.replace(".pdf", "").replace(".json", "").split("_")
            if len(parts) > 1:
                role_title = " ".join(parts[1:4])

        # 2. Company Name
        company = "Unknown Company"
        company_patterns = [
            r"(?:Company|Unternehmen|Arbeitgeber|Firma|Über uns):\s*([A-Za-z0-9\s&.\-]+)",
            r"(?:bei|at|for)\s+([A-Za-z0-9\s&.\-]+(?:GmbH|AG|SE|e\.V\.|Inc\.|LLC|Corp\.|KGaA|Stiftung|Institut))",
            r"([A-Za-z0-9\s&.\-]+(?:GmbH|AG|SE|e\.V\.|Inc\.|LLC|Corp\.|KGaA|Stiftung|Institut))",
            r"(?:at|bei|for)\s+([A-Z][A-Za-z0-9\s&.\-]{2,30})",
        ]
        for pattern in company_patterns:
            match = re.search(pattern, first_few_lines, re.IGNORECASE)
            if match:
                cand = match.group(1).strip(" ,.-:\n\t")
                if len(cand) > 2 and len(cand) < 45 and not cand.lower().startswith("wir suchen"):
                    company = cand
                    break

        if company == "Unknown Company" and "_" in source_filename:
            company = source_filename.split("_")[0]

        # 3. Job ID / Reference code
        job_id_ref = ""
        job_id_match = re.search(
            r"(?:Job-?ID|Ref(?:erenz)?(?:-?Nr\.?|erence)?|Kennziffer|Ausschreibungsnummer|Req(?:uisition)?\s*ID|ID):\s*([A-Za-z0-9\-_/#.]+)",
            text,
            re.IGNORECASE,
        )
        if job_id_match:
            job_id_ref = job_id_match.group(1).strip(" ,.-:\n\t")

        # 4. Location & Work Mode
        location = "Hamburg, Germany"
        loc_patterns = [
            r"(?:Location|Standort|Arbeitsort|Ort):\s*([A-Za-z0-9\s,/\-]+)",
            r"\b(Hamburg|Bergedorf|Potsdam|Berlin|Kiel|Hannover|Bremen|Munich|München|Frankfurt|Köln|Stuttgart|Düsseldorf|Schleswig-Holstein|Niedersachsen)\b",
        ]
        for pattern in loc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                break

        work_mode = "On-site"
        if re.search(r"\b(Remote|Home[- ]?Office|100%\s*Remote)\b", text, re.IGNORECASE):
            work_mode = "Remote"
        elif re.search(r"\b(Hybrid|Mobiles Arbeiten|teilweise Remote)\b", text, re.IGNORECASE):
            work_mode = "Hybrid"

        # 5. Employment Type & Contract Type
        employment_type = "Full-time"
        if re.search(r"\b(Teilzeit|Part-time)\b", text, re.IGNORECASE):
            employment_type = "Part-time"
        elif re.search(r"\b(Vollzeit\s*oder\s*Teilzeit|Full-time\s*or\s*Part-time)\b", text, re.IGNORECASE):
            employment_type = "Full-time / Part-time"
        elif re.search(r"\b(Werkstudent|Working Student|Praktikum|Internship)\b", text, re.IGNORECASE):
            employment_type = "Internship / Student"

        contract_type = "Permanent / Unbefristet"
        if re.search(r"\b(Befristet|Fixed-term|Vertretung)\b", text, re.IGNORECASE):
            contract_type = "Fixed-term / Befristet"

        # Seniority level
        seniority = "Mid-Level"
        if re.search(r"\b(Junior|Entry|Trainee|Absolvent|Einsteiger)\b", role_title + " " + text[:500], re.IGNORECASE):
            seniority = "Junior"
        elif re.search(r"\b(Senior|Lead|Principal|Head of|Leitung)\b", role_title + " " + text[:500], re.IGNORECASE):
            seniority = "Senior / Lead"

        # 6. Deadlines & Day Posted
        deadline = "Open / ASAP"
        deadline_match = re.search(
            r"(?:Bewerbungsfrist|Bewerbungsschluss|Deadline|Apply by|Closing date|Bewerben bis):\s*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        if deadline_match:
            deadline = deadline_match.group(1).strip()

        day_posted = ""
        posted_match = re.search(
            r"(?:Veröffentlicht am|Datum|Posted on|Date posted|Einstellungsdatum):\s*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        if posted_match:
            day_posted = posted_match.group(1).strip()

        start_date = "As soon as possible / Flexible"
        start_match = re.search(
            r"(?:Start date|Starting date|Eintrittsdatum|Beginn|Start(?:\s+ab)?):\s*([A-Za-z0-9\s\.\/]+)",
            text,
            re.IGNORECASE,
        )
        if start_match:
            start_date = start_match.group(1).strip()[:40]

        # 7. Salary / Compensation
        salary_range = "Not disclosed"
        salary_match = re.search(
            r"(?:Gehalt|Vergütung|Salary|Compensation|Entgeltgruppe):\s*([A-Za-z0-9\s€$£,.\-/–]+(?:k|EUR|€|USD|\$|TV-L|TVöD)[A-Za-z0-9\s€$£,.\-/–]*)",
            text,
            re.IGNORECASE,
        )
        if salary_match:
            salary_range = salary_match.group(1).strip()[:40]

        # 8. Contact Person, Email & Phone
        contact_person = ""
        contact_match = re.search(
            r"(?:Ansprechpartner(?:in)?|Kontakt(?:person)?|Contact(?: Person)?|Hiring Manager):\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)",
            text,
            re.IGNORECASE,
        )
        if contact_match:
            contact_person = contact_match.group(1).strip()

        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        contact_email = email_match.group(0) if email_match else ""

        phone_match = re.search(r"(?:\+49|0049|0)\s*[\d\s/\-]{8,20}", text)
        contact_phone = phone_match.group(0).strip() if phone_match else ""

        # 9. Language Requirements
        languages = []
        if re.search(r"\b(German|Deutsch|C1|B2\s*Deutsch|fließend\s*Deutsch)\b", text, re.IGNORECASE):
            languages.append("German (B2/C1)")
        if re.search(r"\b(English|Englisch|fluent\s*English)\b", text, re.IGNORECASE):
            languages.append("English")
        if not languages:
            languages = ["German / English"]

        # 10. Extract skill keywords
        found_skills = []
        lower_text = " " + text.lower() + " "
        for skill in self.known_skills:
            pattern = r"\b" + re.escape(skill.strip()) + r"\b"
            if re.search(pattern, lower_text):
                found_skills.append(skill.strip().capitalize())

        # 11. Extract Structured Sections (Responsibilities, Requirements, Benefits)
        sections = self.extract_sections(text)

        return {
            "source_file": source_filename,
            "company": company,
            "role_title": role_title,
            "job_id_ref": job_id_ref,
            "job_id": job_id_ref,
            "location": location,
            "work_mode": work_mode,
            "employment_type": employment_type,
            "contract_type": contract_type,
            "seniority_level": seniority,
            "deadline": deadline,
            "application_deadline": deadline,
            "day_posted": day_posted,
            "start_date": start_date,
            "salary_range": salary_range,
            "contact_person": contact_person,
            "contact_email": contact_email,
            "contact_phone": contact_phone,
            "languages": ", ".join(languages),
            "extracted_skills": found_skills,
            "key_responsibilities": sections["responsibilities"],
            "responsibilities": sections["responsibilities"],
            "required_qualifications": sections["requirements"],
            "requirements": sections["requirements"],
            "benefits_perks": sections["benefits"],
            "benefits": sections["benefits"],
            "full_text": text,
        }

    def process_pdf(self, pdf_path: Path) -> Dict[str, Any]:
        """Read and parse a single PDF file."""
        text = self.extract_text_from_pdf(pdf_path)
        data = self.parse_job_text(text, pdf_path.name)
        data["pdf_path"] = str(pdf_path)
        return data

    def process_directory(self, dir_path: Path) -> List[Dict[str, Any]]:
        """Process all PDFs in a directory."""
        results = []
        if not dir_path.exists():
            return results

        for pdf_file in dir_path.glob("*.pdf"):
            data = self.process_pdf(pdf_file)
            results.append(data)
        return results
