"""
Job Advertisement Metadata Extractor
Parses PDF files from job_ads_manual/ and job_ads_auto/ using pdfplumber and regex/NLP heuristics
to extract structured fields (Company, Role, Deadline, Skills, Contact, etc.).
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional

import pdfplumber
import pypdf


class JobExtractor:
    def __init__(self):
        # Known common tech and industry keywords to look for
        self.known_skills = [
            # Harsh / Agricultural / Bioeconomy / Sensor Keywords
            "dairy science", "agricultural engineering", "livestock", "ruminant",
            "methane", "ammonia", "nitrous oxide", "co2", "greenhouse gas", "emissions",
            "greenfeed", "gasmet", "ftir", "crds", "tdlas", "pas", "gc-ms",
            "ndir", "gas sensor", "sensor technology", "barn climate", "ventilation",
            "precision livestock farming", "plf", "animal welfare", "herd management",
            "esg", "sustainability", "carbon footprint", "environmental consulting",
            # General Technical / Data / Software Keywords
            "python", " r ", "r studio", "matlab", "sql", "git", "latex", "xelatex",
            "tableau", "power bi", "excel", "docker", "machine learning", "statistics",
            "data analysis", "data science", "time series", "mixed models", "glmm",
            "scrum", "agile", "project management", "rest api", "backend",
            # German skill equivalents
            "milchviehhaltung", "nutztier", "agrartechnik", "stallklima", "gassensorik",
            "datenanalyse", "projektmanagement", "emissionsmessung", "versuchsplanung"
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
        except Exception as e:
            # Fallback to pypdf
            try:
                reader = pypdf.PdfReader(str(pdf_path))
                for page in reader.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text_chunks.append(extracted)
            except Exception as e2:
                print(f"[Extractor] Error reading {pdf_path}: {e2}")

        return "\n".join(text_chunks)

    def parse_job_text(self, text: str, source_filename: str) -> Dict[str, Any]:
        """Extract structured fields from raw text."""
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        first_few_lines = "\n".join(lines[:15])

        # 1. Company Name detection
        company = "Unknown Company"
        company_patterns = [
            r"(?:Company|Unternehmen|Arbeitgeber|Firma|Über uns):\s*([A-Za-z0-9\s&.\-]+)",
            r"([A-Za-z0-9\s&.\-]+(?:GmbH|AG|SE|e\.V\.|Inc\.|LLC|Corp\.|KGaA))",
            r"(?:at|bei|for)\s+([A-Z][A-Za-z0-9\s&.\-]{2,25})"
        ]
        for pattern in company_patterns:
            match = re.search(pattern, first_few_lines, re.IGNORECASE)
            if match:
                cand = match.group(1).strip(" ,.-:\n\t")
                if len(cand) > 2 and len(cand) < 40:
                    company = cand
                    break

        if company == "Unknown Company" and "_" in source_filename:
            company = source_filename.split("_")[0]

        # 2. Role Title detection
        role_title = "Unknown Position"
        title_patterns = [
            r"(?:Position|Job Title|Stellenbezeichnung|Rolle|Wir suchen(?:\s+ab\s+sofort)?(?:\s+einen|\s+eine)?):\s*([A-Za-z0-9\s&./\-\(\)]+)",
            r"((?:Senior\s+|Junior\s+|Lead\s+)?(?:Field Application Specialist|Data Analyst|Data Scientist|Agricultural Engineer|Consultant|Scientist|Project Manager|Software Engineer|Product Manager|Entwickler|Berater|Ingenieur)[A-Za-z0-9\s&./\-\(\)]*)",
        ]
        for pattern in title_patterns:
            match = re.search(pattern, first_few_lines, re.IGNORECASE)
            if match:
                cand = match.group(1).strip(" ,.-:\n\t")
                if len(cand) > 4 and len(cand) < 60:
                    role_title = cand
                    break

        if role_title == "Unknown Position" and "_" in source_filename:
            parts = source_filename.replace(".pdf", "").split("_")
            if len(parts) > 1:
                role_title = " ".join(parts[1:4])

        # 3. Location detection
        location = "Hamburg / Germany"
        loc_patterns = [
            r"(?:Location|Standort|Arbeitsort|Ort):\s*([A-Za-z0-9\s,/\-]+)",
            r"\b(Hamburg|Bergedorf|Potsdam|Berlin|Kiel|Hannover|Bremen|Schleswig-Holstein|Niedersachsen|Remote|Home[- ]Office|Hybrid)\b"
        ]
        for pattern in loc_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                location = match.group(1).strip()
                break

        # 4. Application Deadline
        deadline = "Open / As soon as possible"
        deadline_match = re.search(
            r"(?:Bewerbungsfrist|Bewerbungsschluss|Deadline|Apply by|Closing date):\s*(\d{1,2}[\./\-]\d{1,2}[\./\-]\d{2,4}|\w+\s+\d{1,2},?\s+\d{4})",
            text,
            re.IGNORECASE,
        )
        if deadline_match:
            deadline = deadline_match.group(1).strip()

        # 5. Starting Date
        start_date = "Flexible / Q1 2027 or immediate"
        start_match = re.search(
            r"(?:Start date|Starting date|Eintrittsdatum|Beginn|Start(?:\s+ab)?):\s*([A-Za-z0-9\s\.\/]+)",
            text,
            re.IGNORECASE,
        )
        if start_match:
            start_date = start_match.group(1).strip()[:40]

        # 6. Contract Type
        contract_type = "Full-time / Permanent"
        if re.search(r"(Teilzeit|Part-time)", text, re.IGNORECASE):
            contract_type = "Part-time"
        elif re.search(r"(Befristet|Fixed-term)", text, re.IGNORECASE):
            contract_type = "Fixed-term"
        elif re.search(r"(Vollzeit|Full-time)", text, re.IGNORECASE):
            contract_type = "Full-time"

        # 7. Language Requirements
        languages = []
        if re.search(r"(German|Deutsch|C1|B2\s*Deutsch)", text, re.IGNORECASE):
            languages.append("German (B2/C1)")
        if re.search(r"(English|Englisch)", text, re.IGNORECASE):
            languages.append("English")
        if not languages:
            languages = ["German / English"]

        # 8. Contact & Email extraction
        email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
        contact_email = email_match.group(0) if email_match else ""

        # 9. Skill Keywords matching
        found_skills = []
        lower_text = " " + text.lower() + " "
        for skill in self.known_skills:
            pattern = r"\b" + re.escape(skill.strip()) + r"\b"
            if re.search(pattern, lower_text):
                found_skills.append(skill.strip())

        return {
            "source_file": source_filename,
            "company": company,
            "role_title": role_title,
            "location": location,
            "deadline": deadline,
            "start_date": start_date,
            "contract_type": contract_type,
            "languages": ", ".join(languages),
            "contact_email": contact_email,
            "extracted_skills": found_skills,
            "raw_text_preview": lines[:5],
            "full_text": text
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
            print(f"[Extractor] Parsing: {pdf_file.name}")
            data = self.process_pdf(pdf_file)
            results.append(data)
        return results
