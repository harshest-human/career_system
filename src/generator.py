"""
Dynamic LaTeX CV and Cover Letter Generator
Renders Jinja2-LaTeX templates with candidate profile data and job-specific tailoring,
then compiles final PDFs using XeLaTeX.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import jinja2
import yaml


def escape_latex(val: Any) -> Any:
    """Escapes special LaTeX characters in strings."""
    if not isinstance(val, str):
        return val

    # Avoid double escaping already escaped sequences
    # Replacements order matters: backslash first if needed, then specials
    specials = {
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    # Don't replace if it's already LaTeX command
    for char, replacement in specials.items():
        # Negative lookbehind to not replace if already backslashed
        val = re.sub(r"(?<!\\)" + re.escape(char), replacement, val)
    return val


def sanitize_dict_for_latex(data: Any) -> Any:
    """Recursively escape strings inside nested dictionaries/lists for LaTeX safety."""
    if isinstance(data, dict):
        return {k: sanitize_dict_for_latex(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [sanitize_dict_for_latex(v) for v in data]
    elif isinstance(data, str):
        return escape_latex(data)
    return data


class DocumentGenerator:
    def __init__(
        self,
        profiles_dir: Path = Path("profiles"),
        templates_dir: Path = Path("latex_generator/templates"),
        outputs_dir: Path = Path("outputs"),
    ):
        self.profiles_dir = profiles_dir
        self.templates_dir = templates_dir
        self.outputs_dir = outputs_dir

        # Setup Jinja2 environment with LaTeX-friendly delimiters
        self.jinja_env = jinja2.Environment(
            block_start_string="<%",
            block_end_string="%>",
            variable_start_string="<<",
            variable_end_string=">>",
            comment_start_string="<#",
            comment_end_string="#>",
            loader=jinja2.FileSystemLoader(str(self.templates_dir)),
            autoescape=False,
        )

        # Locate LaTeX compiler
        self.compiler = shutil.which("xelatex") or shutil.which("pdflatex")
        if not self.compiler:
            # Check standard MiKTeX path on Windows
            miktex_path = Path(r"C:\Program Files\MiKTeX\miktex\bin\x64\xelatex.exe")
            if miktex_path.exists():
                self.compiler = str(miktex_path)

    def load_profile(self, candidate_id: str) -> Dict[str, Any]:
        """Load candidate profile configuration."""
        profile_path = self.profiles_dir / candidate_id / "profile.yaml"
        if not profile_path.exists():
            raise FileNotFoundError(f"Profile not found: {profile_path}")
        with open(profile_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_bullets(self, candidate_id: str, lang: str = "en") -> Dict[str, Any]:
        """Load candidate bullet repositories."""
        bullets_path = self.profiles_dir / candidate_id / f"bullets_{lang}.yaml"
        if not bullets_path.exists():
            return {}
        with open(bullets_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def tailor_cv_context(
        self,
        profile: Dict[str, Any],
        bullets_repo: Dict[str, Any],
        job_data: Dict[str, Any],
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Dynamically assemble and customize CV sections based on job requirements."""
        personal = profile.get("personal", {})
        job_skills = [s.lower() for s in job_data.get("extracted_skills", [])]

        # 1. Tailor Executive Summary
        exec_summary = profile.get("executive_summary", {}).get(lang, "")

        # 2. Tailor Experience Bullets
        experience_list = []
        for exp in profile.get("experience", []):
            cat = exp.get("category", "default")
            repo_section = bullets_repo.get(cat, {})

            # Select bullets based on keyword overlap
            selected_bullets = []
            if any(k in job_skills for k in ["r", "python", "statistics", "data analysis", "datenanalyse"]):
                selected_bullets.extend(repo_section.get("data_analysis_focus", []))
            if any(k in job_skills for k in ["gasmet", "sensor", "hardware", "greenfeed", "ftir", "crds"]):
                selected_bullets.extend(repo_section.get("hardware_field_focus", []))
                selected_bullets.extend(repo_section.get("hardware_focus", []))
            if any(k in job_skills for k in ["esg", "sustainability", "consulting", "carbon footprint"]):
                selected_bullets.extend(repo_section.get("esg_sustainability_focus", []))

            # Default fallback bullets
            default_bullets = repo_section.get("default", [])
            for b in default_bullets:
                if b not in selected_bullets:
                    selected_bullets.append(b)

            # Cap bullets per role to 3-4 for concise 1-2 page layout
            selected_bullets = selected_bullets[:4]

            role_title = exp.get(f"role_{lang}", exp.get("role_en", ""))
            period = exp.get(f"period_{lang}", exp.get("period_en", ""))
            inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))

            experience_list.append({
                "role": role_title,
                "period": period,
                "institution": inst,
                "affiliation": exp.get("affiliation", ""),
                "bullets": selected_bullets,
            })

        # 3. Education
        education_list = []
        for edu in profile.get("education", []):
            education_list.append({
                "degree": edu.get(f"degree_{lang}", edu.get("degree_en", "")),
                "period": edu.get(f"period_{lang}", edu.get("period_en", "")),
                "institution": edu.get("institution", ""),
                "notes": edu.get(f"notes_{lang}", edu.get("notes_en", "")),
            })

        # 4. Skills format
        skills_raw = profile.get("skills", {})
        skills_formatted = {
            "domains": ", ".join(skills_raw.get("domains", [])),
            "hardware": ", ".join(skills_raw.get("hardware_instruments", [])),
            "software": ", ".join(skills_raw.get("software_tools", [])),
            "languages": ", ".join(
                f"{l.get('language')} ({l.get('level')})" for l in skills_raw.get("languages", [])
            ),
        }

        # 5. References format
        refs = profile.get("references", [])
        ref_str = ", ".join(f"{r.get('name')} ({r.get('role')})" for r in refs)

        context = {
            "personal": personal,
            "executive_summary": exec_summary,
            "experience": experience_list,
            "education": education_list,
            "skills": skills_formatted,
            "leadership": profile.get("leadership_awards", []),
            "references": ref_str,
            "job": job_data,
        }

        return sanitize_dict_for_latex(context)

    def tailor_cover_letter_context(
        self,
        profile: Dict[str, Any],
        job_data: Dict[str, Any],
        lang: str = "en",
        custom_paragraphs: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Generate tailored cover letter paragraphs matching company and role requirements."""
        personal = profile.get("personal", {})
        company = job_data.get("company", "the Company")
        role = job_data.get("role_title", "Position")
        candidate_name = personal.get("full_name", "")

        today_str = datetime.now().strftime("%d %B %Y" if lang == "en" else "%d. %B %Y")
        salutation = (
            f"Dear {job_data.get('hiring_manager', 'Hiring Team')},"
            if lang == "en"
            else f"Sehr geehrte(r) {job_data.get('hiring_manager', 'Damen und Herren')},"
        )

        if custom_paragraphs and len(custom_paragraphs) > 0:
            paragraphs = [p for p in custom_paragraphs if p and p.strip()]
        elif lang == "en":
            paragraphs = [
                (
                    f"I am writing to express my strong interest in the {role} position at {company}. "
                    f"With my background in agricultural engineering, dairy science, and hands-on "
                    f"sensor and data analytics experience at Leibniz ATB, I offer a unique combination "
                    f"of scientific rigor and practical industry application."
                ),
                (
                    f"In my current doctoral research and past projects, I have led field campaigns in commercial "
                    f"dairy barns, developed low-cost gas sensing systems, and integrated complex environmental and herd datasets. "
                    f"This experience aligns closely with {company}'s focus on innovation, technical reliability, and sustainable production."
                ),
                (
                    f"I am particularly excited about the opportunity to contribute to {company} by bringing deep expertise "
                    f"in measurement technology, statistical modeling in R/Python, and clear stakeholder communication. "
                    f"I hold permanent residence in Germany and am available for both on-site field visits and collaborative project work."
                ),
                (
                    f"Thank you for considering my application. I look forward to discussing how my background and enthusiasm "
                    f"can support {company}'s continued success."
                ),
            ]
        else:
            paragraphs = [
                (
                    f"mit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}. "
                    f"Mit meinem fundierten Hintergrund in Agrartechnik, Milchwissenschaften und mehrjähriger "
                    f"Forschungserfahrung am Leibniz-Institut für Agrartechnik und Bioökonomie (ATB) verbinde ich "
                    f"wissenschaftliche Methodik mit praxisorientierter technischer Umsetzung."
                ),
                (
                    f"Im Rahmen meiner Promotion und Projektarbeit habe ich Feldversuche in Praxisbetrieben geleitet, "
                    f"skalierbare Sensorsysteme entwickelt und umfangreiche Mess- sowie Herdenmanagementdaten analysiert. "
                    f"Diese Erfahrungen passen ideal zu den Anforderungen und Innovationszielen von {company}."
                ),
                (
                    f"Ich freue mich darauf, meine Kenntnisse in Sensortechnologie, Datenanalyse (R/Python) und "
                    f"der zielgerichteten Kommunikation mit Praxispartnern gewinnbringend bei {company} einzubringen. "
                    f"Ich verfüge über eine unbefristete Aufenthalts- und Arbeitserlaubnis in Deutschland."
                ),
                (
                    f"Über die Gelegenheit, mich Ihnen in einem persönlichen Gespräch vorzustellen, freue ich mich sehr."
                ),
            ]

        context = {
            "personal": personal,
            "job": {
                "company": company,
                "role_title": role,
                "city": job_data.get("location", "Hamburg"),
                "hiring_manager": job_data.get("hiring_manager", ""),
                "req_id": job_data.get("req_id", ""),
            },
            "date": today_str,
            "salutation": salutation,
            "letter_body": paragraphs,
        }

        return sanitize_dict_for_latex(context)

    def compile_pdf(self, tex_file: Path, output_dir: Path) -> Optional[Path]:
        """Compile .tex file to PDF using XeLaTeX with 2 passes for layout stability."""
        if not self.compiler:
            print("[Generator] Error: XeLaTeX compiler not found on PATH or MiKTeX directory.")
            return None

        cmd = [
            self.compiler,
            "-interaction=nonstopmode",
            "-halt-on-error",
            tex_file.name,
        ]

        for pass_num in (1, 2):
            try:
                res = subprocess.run(
                    cmd,
                    cwd=str(output_dir.resolve()),
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    timeout=90,
                )
                if res.returncode != 0:
                    print(f"[Generator] LaTeX Error (pass {pass_num}):\n{res.stdout}")
                    return None
            except Exception as e:
                print(f"[Generator] Compilation exception: {e}")
                return None

        pdf_name = tex_file.stem + ".pdf"
        pdf_path = output_dir / pdf_name
        if pdf_path.exists():
            return pdf_path.resolve()
        return None

    def generate_documents(
        self,
        candidate_id: str,
        job_data: Dict[str, Any],
        lang: str = "en",
        custom_summary: Optional[str] = None,
        custom_letter_paragraphs: Optional[List[str]] = None,
    ) -> Dict[str, Path]:
        """Generate tailored CV and Cover Letter .tex and compile them to PDFs."""
        profile = self.load_profile(candidate_id)
        bullets_repo = self.load_bullets(candidate_id, lang)

        if custom_summary:
            profile.setdefault("executive_summary", {})[lang] = custom_summary

        # Setup destination directory
        company_slug = re.sub(r"[^\w\-]", "_", job_data.get("company", "Company"))
        role_slug = re.sub(r"[^\w\-]", "_", job_data.get("role_title", "Role"))
        target_dir = (self.outputs_dir / candidate_id / f"{company_slug}_{role_slug}_{lang}").resolve()
        target_dir.mkdir(parents=True, exist_ok=True)

        # Copy style.tex to target_dir so relative input works seamlessly
        shutil.copy(self.templates_dir / "style.tex", target_dir / "style.tex")

        # 1. Render CV
        cv_context = self.tailor_cv_context(profile, bullets_repo, job_data, lang)
        cv_template_name = f"cv_{lang}.tex"
        cv_template = self.jinja_env.get_template(cv_template_name)
        cv_tex_content = cv_template.render(cv_context)

        cv_tex_path = target_dir / f"CV_{profile['personal']['full_name'].replace(' ', '_')}_{lang}.tex"
        with open(cv_tex_path, "w", encoding="utf-8") as f:
            f.write(cv_tex_content)

        cv_pdf = self.compile_pdf(cv_tex_path, target_dir)

        # 2. Render Cover Letter
        letter_context = self.tailor_cover_letter_context(profile, job_data, lang, custom_letter_paragraphs)
        letter_template_name = f"letter_{lang}.tex"
        letter_template = self.jinja_env.get_template(letter_template_name)
        letter_tex_content = letter_template.render(letter_context)

        letter_tex_path = target_dir / f"CoverLetter_{profile['personal']['full_name'].replace(' ', '_')}_{lang}.tex"
        with open(letter_tex_path, "w", encoding="utf-8") as f:
            f.write(letter_tex_content)

        letter_pdf = self.compile_pdf(letter_tex_path, target_dir)

        print(f"[Generator] Documents generated for '{candidate_id}' in {target_dir}:")
        if cv_pdf:
            print(f"  - CV:           {cv_pdf}")
        if letter_pdf:
            print(f"  - Cover Letter: {letter_pdf}")

        return {
            "cv_tex": cv_tex_path,
            "cv_pdf": cv_pdf,
            "letter_tex": letter_tex_path,
            "letter_pdf": letter_pdf,
        }
