"""
HTML & CSS Resume and Cover Letter Template Engine
Produces clean, modern, ATS-compliant HTML/CSS documents in English (UK) and Deutsch.
Strictly calibrated for standard ISO 216 A4 Paper dimensions (210mm x 297mm).
Refined Blueish & Blue-Gray Accent Theme.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional


def render_html_cv(
    profile: Dict[str, Any],
    job_data: Dict[str, Any],
    lang: str = "en",
    custom_summary: Optional[str] = None,
) -> str:
    """Render a complete, self-contained HTML/CSS CV strictly sized for A4 in English (UK) or Deutsch."""
    is_de = (lang.lower() == "de")
    personal = profile.get("personal", {})
    full_name = personal.get("full_name", "Applicant Name")
    title = personal.get(f"title_{lang}", personal.get("title_en", ""))
    city = personal.get(f"city_{lang}", personal.get("city_en", ""))
    phone = personal.get("phone", "")
    email = personal.get("email", "")
    linkedin = personal.get("linkedin_url", "")
    github = personal.get("github_url", "")
    work_auth = personal.get("residence_status", "")

    summary = custom_summary or profile.get("executive_summary", {}).get(lang, "")
    experiences = profile.get("experience", [])
    educations = profile.get("education", [])
    skills = profile.get("skills", {})
    leadership = profile.get("leadership_awards", [])

    # Localized Labels
    labels = {
        "profile": "Executive Profile" if not is_de else "Profil & Zusammenfassung",
        "experience": "Professional Experience" if not is_de else "Berufserfahrung",
        "education": "Education & Qualifications" if not is_de else "Ausbildung & Studium",
        "skills": "Core Competencies & Skills" if not is_de else "Fachkenntnisse & Methoden",
        "domains": "Core Domains" if not is_de else "Fachgebiete",
        "software": "Software & Tools" if not is_de else "Software & Tools",
        "hardware": "Technical Instrumentation" if not is_de else "Messtechnik & Hardware",
        "languages": "Languages" if not is_de else "Sprachkenntnisse",
        "leadership": "Key Credentials & Awards" if not is_de else "Zusatzqualifikationen & Auszeichnungen",
        "work_auth": "Work Authorisation" if not is_de else "Arbeitserlaubnis",
    }

    # Format Experience Items
    exp_html = ""
    for exp in experiences:
        role = exp.get(f"role_{lang}", exp.get("role_en", ""))
        period = exp.get(f"period_{lang}", exp.get("period_en", ""))
        inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))
        aff = exp.get("affiliation", "")

        bullets_html = ""
        for b in exp.get("bullets", []):
            bullets_html += f"<li>{b}</li>\n"

        exp_html += f"""
        <div class="entry">
          <div class="entry-header">
            <div class="entry-title">{role}</div>
            <div class="entry-date">{period}</div>
          </div>
          <div class="entry-sub">
            <span>{inst}</span>
            {f'<span class="entry-aff">{aff}</span>' if aff else ''}
          </div>
          <ul class="cv-bullets">
            {bullets_html}
          </ul>
        </div>
        """

    # Format Education Items
    edu_html = ""
    for edu in educations:
        degree = edu.get(f"degree_{lang}", edu.get("degree_en", ""))
        period = edu.get(f"period_{lang}", edu.get("period_en", ""))
        inst = edu.get("institution", "")
        notes = edu.get(f"notes_{lang}", edu.get("notes_en", ""))

        edu_html += f"""
        <div class="entry">
          <div class="entry-header">
            <div class="entry-title">{degree}</div>
            <div class="entry-date">{period}</div>
          </div>
          <div class="entry-sub">{inst}</div>
          {f'<div class="entry-notes">{notes}</div>' if notes else ''}
        </div>
        """

    # Format Skills
    domains_str = ", ".join(skills.get("domains", []))
    software_str = ", ".join(skills.get("software_tools", []))
    hardware_str = ", ".join(skills.get("hardware_instruments", []))
    langs_str = ", ".join(f"{l.get('language')} ({l.get('level')})" for l in skills.get("languages", []))

    # Format Leadership
    lead_html = ""
    for item in leadership:
        lead_html += f"<li>{item}</li>"

    html_doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Curriculum Vitae - {full_name}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      background: #f8fafc;
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
      font-size: 9.5pt;
      line-height: 1.45;
      color: #1e293b;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .cv-page {{
      width: 210mm;
      min-height: 297mm;
      box-sizing: border-box;
      padding: 14mm 16mm 14mm 16mm;
      margin: 0 auto 10mm auto;
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}
    /* Header */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2.5px solid #2563eb;
      padding-bottom: 8px;
      margin-bottom: 12px;
    }}
    .header-left .name {{
      font-size: 20pt;
      font-weight: 800;
      color: #1e3a8a;
      letter-spacing: -0.5px;
      line-height: 1.1;
    }}
    .header-left .headline {{
      font-size: 10.5pt;
      font-weight: 600;
      color: #334155;
      margin-top: 3px;
    }}
    .header-right {{
      text-align: right;
      font-size: 8.5pt;
      color: #475569;
      line-height: 1.45;
    }}
    .header-right a {{
      color: #2563eb;
      text-decoration: none;
      font-weight: 500;
    }}
    /* Section */
    .section {{
      margin-bottom: 11px;
    }}
    .section-title {{
      font-size: 9.5pt;
      font-weight: 700;
      color: #1e3a8a;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      border-bottom: 1px solid #cbd5e1;
      padding-bottom: 2px;
      margin-bottom: 6px;
    }}
    .summary-text {{
      font-size: 9pt;
      color: #334155;
      text-align: justify;
      line-height: 1.42;
    }}
    /* Entry */
    .entry {{
      margin-bottom: 8px;
    }}
    .entry-header {{
      display: flex;
      justify-content: space-between;
      align-items: baseline;
    }}
    .entry-title {{
      font-weight: 700;
      font-size: 9.5pt;
      color: #0f172a;
    }}
    .entry-date {{
      font-size: 8.5pt;
      font-weight: 600;
      color: #475569;
    }}
    .entry-sub {{
      font-size: 8.5pt;
      font-style: italic;
      color: #475569;
      display: flex;
      justify-content: space-between;
      margin-bottom: 3px;
    }}
    .entry-notes {{
      font-size: 8.5pt;
      color: #475569;
      margin-top: 1px;
    }}
    /* Bullets */
    .cv-bullets {{
      margin-left: 14px;
      padding-left: 0;
      font-size: 8.5pt;
      color: #334155;
      line-height: 1.35;
    }}
    .cv-bullets li {{
      margin-bottom: 2.5px;
    }}
    /* Skills */
    .skill-line {{
      font-size: 8.5pt;
      color: #334155;
      margin-bottom: 3px;
    }}
    .skill-line strong {{
      color: #0f172a;
    }}
    @media print {{
      html, body {{
        background: #ffffff;
        margin: 0;
        padding: 0;
        width: 210mm;
      }}
      .cv-page {{
        margin: 0;
        padding: 14mm 16mm 14mm 16mm;
        box-shadow: none;
        page-break-after: always;
      }}
    }}
  </style>
</head>
<body>
  <div class="cv-page">
    <div class="header">
      <div class="header-left">
        <div class="name">{full_name}</div>
        <div class="headline">{title}</div>
      </div>
      <div class="header-right">
        <div>{city} &bull; {phone}</div>
        <div><a href="mailto:{email}">{email}</a></div>
        <div><a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
      </div>
    </div>

    {f'''<div class="section">
      <div class="section-title">{labels['profile']}</div>
      <div class="summary-text">{summary}</div>
    </div>''' if summary else ''}

    <div class="section">
      <div class="section-title">{labels['experience']}</div>
      {exp_html}
    </div>

    <div class="section">
      <div class="section-title">{labels['education']}</div>
      {edu_html}
    </div>

    <div class="section">
      <div class="section-title">{labels['skills']}</div>
      <div class="skill-line"><strong>{labels['domains']}:</strong> {domains_str}</div>
      {f'<div class="skill-line"><strong>{labels["hardware"]}:</strong> {hardware_str}</div>' if hardware_str else ''}
      <div class="skill-line"><strong>{labels['software']}:</strong> {software_str}</div>
      <div class="skill-line"><strong>{labels['languages']}:</strong> {langs_str}</div>
    </div>

    {f'''<div class="section">
      <div class="section-title">{labels['leadership']}</div>
      <ul class="cv-bullets" style="margin-bottom: 4px;">{lead_html}</ul>
      {f'<div class="skill-line"><strong>{labels["work_auth"]}:</strong> {work_auth}</div>' if work_auth else ''}
    </div>''' if leadership or work_auth else ''}
  </div>
</body>
</html>
"""
    return html_doc


def render_html_cover_letter(
    profile: Dict[str, Any],
    job_data: Dict[str, Any],
    lang: str = "en",
    custom_paragraphs: Optional[List[str]] = None,
) -> str:
    """Render a complete, self-contained HTML/CSS Cover Letter strictly sized for A4 in English (UK) or Deutsch."""
    is_de = (lang.lower() == "de")
    personal = profile.get("personal", {})
    full_name = personal.get("full_name", "Applicant Name")
    city = personal.get(f"city_{lang}", personal.get("city_en", ""))
    phone = personal.get("phone", "")
    email = personal.get("email", "")
    linkedin = personal.get("linkedin_url", "")

    company = job_data.get("company", "Target Company")
    role = job_data.get("role_title", "Position")
    job_city = job_data.get("location", "Location")
    hiring_manager = job_data.get("hiring_manager_contact") or job_data.get("hiring_manager", "")
    req_id = job_data.get("job_id") or job_data.get("job_id_ref", "")

    # Date formatting
    if is_de:
        today_str = datetime.now().strftime("%d. %B %Y")
        salutation = f"Sehr geehrte(r) {hiring_manager}," if hiring_manager else "Sehr geehrte Damen und Herren,"
        closing = "Mit freundlichen Grüßen,"
        subject_prefix = "Bewerbung als "
    else:
        # UK Date format
        today_str = datetime.now().strftime("%d %B %Y")
        salutation = f"Dear {hiring_manager}," if hiring_manager else "Dear Hiring Team,"
        closing = "Yours sincerely,"
        subject_prefix = "Application for the position of "

    if custom_paragraphs and len(custom_paragraphs) > 0:
        paragraphs = [p for p in custom_paragraphs if p and p.strip()]
    elif is_de:
        paragraphs = [
            f"mit großem Interesse bewerbe ich mich auf die Position als {role} bei {company}. Mein Profil verbindet fundierte Fachkenntnisse mit einer lösungsorientierten und strukturierten Arbeitsweise.",
            f"In meinen bisherigen Projekten und Verantwortungsbereichen habe ich maßgebliche Aufgaben erfolgreich gesteuert, datengestützte Prozesse optimiert und eng mit interdisziplinären Teams zusammengearbeitet.",
            f"Ich verfüge über eine uneingeschränkte Arbeitserlaubnis in Deutschland und freue mich auf die Gelegenheit, mich Ihnen in einem persönlichen Gespräch vorzustellen.",
        ]
    else:
        paragraphs = [
            f"I am writing to express my strong interest in the {role} position at {company}. My professional background and proven hands-on execution directly align with your team's current operational goals.",
            f"In my previous work, I have successfully led key initiatives, streamlined analytical workflows, and collaborated cross-functionally to achieve measurable results.",
            f"I hold valid work authorization in Germany and look forward to discussing how my experience can support {company}'s ongoing success.",
        ]

    paras_html = "".join(f"<p class='letter-para'>{p}</p>" for p in paragraphs)

    html_doc = f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Cover Letter - {full_name} - {company}</title>
  <style>
    @page {{
      size: A4 portrait;
      margin: 0;
    }}
    * {{
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }}
    html, body {{
      width: 210mm;
      min-height: 297mm;
      margin: 0 auto;
      background: #f8fafc;
      font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif;
      font-size: 10.5pt;
      line-height: 1.55;
      color: #1e293b;
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .letter-page {{
      width: 210mm;
      min-height: 297mm;
      box-sizing: border-box;
      padding: 20mm 20mm 20mm 20mm;
      margin: 0 auto 10mm auto;
      background: #ffffff;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #2563eb;
      padding-bottom: 10px;
      margin-bottom: 20px;
    }}
    .name {{
      font-size: 19pt;
      font-weight: 800;
      color: #1e3a8a;
      letter-spacing: -0.5px;
    }}
    .contact-info {{
      text-align: right;
      font-size: 9pt;
      color: #475569;
      line-height: 1.4;
    }}
    .contact-info a {{
      color: #2563eb;
      text-decoration: none;
    }}
    .recipient {{
      margin-bottom: 16px;
      font-size: 10pt;
      color: #334155;
      line-height: 1.4;
    }}
    .date-line {{
      margin-bottom: 16px;
      font-size: 10pt;
      color: #64748b;
    }}
    .subject-line {{
      font-size: 11.5pt;
      font-weight: 700;
      color: #0f172a;
      margin-bottom: 16px;
    }}
    .salutation {{
      margin-bottom: 14px;
      font-weight: 600;
    }}
    .letter-para {{
      margin-bottom: 14px;
      text-align: justify;
      color: #334155;
    }}
    .closing {{
      margin-top: 22px;
      margin-bottom: 26px;
    }}
    .signature-name {{
      font-weight: 700;
      color: #0f172a;
    }}
    @media print {{
      html, body {{
        background: #ffffff;
        margin: 0;
        padding: 0;
        width: 210mm;
      }}
      .letter-page {{
        margin: 0;
        padding: 20mm 20mm 20mm 20mm;
        box-shadow: none;
        page-break-after: always;
      }}
    }}
  </style>
</head>
<body>
  <div class="letter-page">
    <div class="header">
      <div class="name">{full_name}</div>
      <div class="contact-info">
        <div>{city} &bull; {phone}</div>
        <div><a href="mailto:{email}">{email}</a></div>
        <div><a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
      </div>
    </div>

    <div class="recipient">
      <strong>{company}</strong><br>
      {hiring_manager + '<br>' if hiring_manager else ''}
      {job_city}
    </div>

    <div class="date-line">{today_str}</div>

    <div class="subject-line">
      {subject_prefix}{role}
      {f'<span style="font-size: 9pt; font-weight: normal; color: #64748b; float: right;">Ref: {req_id}</span>' if req_id else ''}
    </div>

    <div class="salutation">{salutation}</div>

    {paras_html}

    <div class="closing">{closing}</div>
    <div class="signature-name">{full_name}</div>
  </div>
</body>
</html>
"""
    return html_doc
