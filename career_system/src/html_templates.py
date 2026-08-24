"""
HTML & CSS Resume and Cover Letter Template Engine
Produces 3 Minimalist European-Style ATS-Compliant Designs:
1. Zurich Minimalist (Swiss Elegance - Clean Linear Grid, Universal ATS 100%)
2. Berlin Executive (German Corporate 2-Column Split Layout with Accent Sidebar)
3. Stockholm Tech (Nordic Modern - Borderless Timeline & Tech Badges)

Strictly calibrated for standard ISO 216 A4 Paper dimensions (210mm x 297mm).
Supports optional profile picture and bilingual (EN/DE) rendering.
"""

from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional


def get_labels(lang: str) -> Dict[str, str]:
    is_de = (lang.lower() == "de")
    return {
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
        "contact": "Contact Details" if not is_de else "Kontaktdaten",
    }


def resolve_photo_src(profile: Dict[str, Any], job_data: Dict[str, Any], photo_src: Optional[str] = None) -> str:
    personal = profile.get("personal", {})
    return str(
        photo_src
        or job_data.get("photo_src")
        or job_data.get("photo_base64")
        or job_data.get("photo_url")
        or personal.get("photo_src")
        or personal.get("photo_base64")
        or personal.get("photo_url")
        or personal.get("photo")
        or ""
    ).strip()


def render_html_cv(
    profile: Dict[str, Any],
    job_data: Dict[str, Any],
    lang: str = "en",
    design: str = "zurich",
    custom_summary: Optional[str] = None,
    photo_src: Optional[str] = None,
) -> str:
    """Render a complete, self-contained HTML/CSS CV in one of 3 European ATS-friendly styles."""
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

    resolved_photo = resolve_photo_src(profile, job_data, photo_src)
    labels = get_labels(lang)

    summary = custom_summary or profile.get("executive_summary", {}).get(lang, "")
    experiences = profile.get("experience", [])
    educations = profile.get("education", [])
    skills = profile.get("skills", {})
    leadership = profile.get("leadership_awards", [])

    # Format Skills
    domains_raw = skills.get("domains", [])
    domains_str = ", ".join(domains_raw) if isinstance(domains_raw, list) else str(domains_raw or "")

    software_raw = skills.get("software_tools", [])
    software_str = ", ".join(software_raw) if isinstance(software_raw, list) else str(software_raw or "")

    hardware_raw = skills.get("hardware_instruments", [])
    hardware_str = ", ".join(hardware_raw) if isinstance(hardware_raw, list) else str(hardware_raw or "")

    langs_raw = skills.get("languages", [])
    if isinstance(langs_raw, list):
        langs_str = ", ".join(f"{l.get('language')} ({l.get('level')})" if isinstance(l, dict) else str(l) for l in langs_raw)
    else:
        langs_str = str(langs_raw or "")

    leadership_raw = leadership if isinstance(leadership, list) else [l.strip() for l in str(leadership).split("\n") if l.strip()]
    lead_str = " &bull; ".join(leadership_raw[:4])

    # DESIGN 1: ZURICH SWISS MINIMALIST (Clean Linear Grid)
    if design.lower() == "zurich":
        photo_html = f'<div class="photo-box"><img src="{resolved_photo}" alt="{full_name}"></div>' if resolved_photo else ""
        
        exp_html = ""
        for exp in experiences[:5]:
            role = exp.get(f"role_{lang}", exp.get("role_en", ""))
            period = exp.get(f"period_{lang}", exp.get("period_en", ""))
            inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))
            aff = exp.get("affiliation", "")
            bullets = exp.get("bullets", [])
            bullets_html = "".join(f"<li>{b}</li>" for b in bullets[:3])
            
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
              <ul class="cv-bullets">{bullets_html}</ul>
            </div>"""

        edu_html = ""
        for edu in educations[:2]:
            degree = edu.get(f"degree_{lang}", edu.get("degree_en", ""))
            period = edu.get(f"period_{lang}", edu.get("period_en", ""))
            inst = edu.get("institution", "")
            notes = edu.get(f"notes_{lang}", edu.get("notes_en", ""))
            edu_html += f"""
            <div class="entry" style="margin-bottom: 3px;">
              <div class="entry-header">
                <div class="entry-title">{degree}</div>
                <div class="entry-date">{period}</div>
              </div>
              <div class="entry-sub">
                <span>{inst}</span>
                {f'<span class="entry-notes"> &bull; {notes}</span>' if notes else ''}
              </div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Curriculum Vitae - {full_name}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.5pt; line-height: 1.32; color: #1e293b; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; padding: 10mm 13mm; margin: 0 auto; background: #ffffff; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }}
    .header {{ display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #2563eb; padding-bottom: 7px; margin-bottom: 8px; }}
    .header-left-wrap {{ display: flex; align-items: center; gap: 10px; }}
    .photo-box {{ width: 52px; height: 52px; min-width: 52px; max-width: 52px; aspect-ratio: 1/1; border-radius: 6px; border: 1.5px solid #2563eb; overflow: hidden; background: #f1f5f9; }}
    .photo-box img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .header-left .name {{ font-size: 17pt; font-weight: 800; color: #1e3a8a; letter-spacing: -0.4px; line-height: 1.1; }}
    .header-left .headline {{ font-size: 9pt; font-weight: 600; color: #334155; margin-top: 2px; }}
    .header-right {{ text-align: right; font-size: 7.8pt; color: #475569; line-height: 1.35; }}
    .header-right a {{ color: #2563eb; text-decoration: none; font-weight: 500; }}
    .section {{ margin-bottom: 6px; }}
    .section-title {{ font-size: 8.5pt; font-weight: 700; color: #1e3a8a; text-transform: uppercase; letter-spacing: 0.4px; border-bottom: 1px solid #cbd5e1; padding-bottom: 1.5px; margin-bottom: 4px; }}
    .summary-text {{ font-size: 8.2pt; color: #334155; text-align: justify; line-height: 1.3; }}
    .entry {{ margin-bottom: 4px; }}
    .entry-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
    .entry-title {{ font-weight: 700; font-size: 8.5pt; color: #0f172a; }}
    .entry-date {{ font-size: 7.8pt; font-weight: 600; color: #475569; }}
    .entry-sub {{ font-size: 7.8pt; font-style: italic; color: #475569; display: flex; justify-content: space-between; margin-bottom: 1.5px; }}
    .cv-bullets {{ margin-left: 12px; padding-left: 0; font-size: 7.8pt; color: #334155; line-height: 1.26; }}
    .cv-bullets li {{ margin-bottom: 1px; }}
    .skill-line {{ font-size: 7.8pt; color: #334155; margin-bottom: 2px; line-height: 1.25; }}
    .skill-line strong {{ color: #0f172a; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; padding: 10mm 13mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="cv-page cv-design-zurich">
    <div class="header">
      <div class="header-left-wrap">
        {photo_html}
        <div class="header-left">
          <div class="name">{full_name}</div>
          <div class="headline">{title}</div>
        </div>
      </div>
      <div class="header-right">
        <div>{city} &bull; {phone}</div>
        <div><a href="mailto:{email}">{email}</a></div>
        <div><a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
      </div>
    </div>

    {f'<div class="section"><div class="section-title">{labels["profile"]}</div><div class="summary-text">{summary}</div></div>' if summary else ''}

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

    {f'<div class="section"><div class="section-title">{labels["leadership"]}</div><div class="skill-line">{lead_str}</div>{f"<div class='skill-line' style='margin-top: 2px;'><strong>{labels['work_auth']}:</strong> {work_auth}</div>" if work_auth else ""}</div>' if lead_str or work_auth else ''}
  </div>
</body>
</html>"""

    # DESIGN 2: BERLIN EXECUTIVE (Modern European 2-Column Split)
    elif design.lower() == "berlin":
        photo_html = f'<div class="berlin-photo"><img src="{resolved_photo}" alt="{full_name}"></div>' if resolved_photo else ""
        
        exp_html = ""
        for exp in experiences[:5]:
            role = exp.get(f"role_{lang}", exp.get("role_en", ""))
            period = exp.get(f"period_{lang}", exp.get("period_en", ""))
            inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))
            bullets = exp.get("bullets", [])
            bullets_html = "".join(f"<li>{b}</li>" for b in bullets[:3])
            exp_html += f"""
            <div class="berlin-exp-item">
              <div class="berlin-exp-header">
                <span class="berlin-exp-role">{role}</span>
                <span class="berlin-exp-date">{period}</span>
              </div>
              <div class="berlin-exp-inst">{inst}</div>
              <ul class="berlin-bullets">{bullets_html}</ul>
            </div>"""

        edu_html = ""
        for edu in educations[:2]:
            degree = edu.get(f"degree_{lang}", edu.get("degree_en", ""))
            period = edu.get(f"period_{lang}", edu.get("period_en", ""))
            inst = edu.get("institution", "")
            edu_html += f"""
            <div class="berlin-edu-item">
              <div class="berlin-exp-header">
                <span class="berlin-exp-role">{degree}</span>
                <span class="berlin-exp-date">{period}</span>
              </div>
              <div class="berlin-exp-inst">{inst}</div>
            </div>"""

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Curriculum Vitae - {full_name}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.4pt; line-height: 1.3; color: #1e293b; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; margin: 0 auto; background: #ffffff; display: flex; flex-direction: row; overflow: hidden; }}
    .berlin-sidebar {{ width: 68mm; min-width: 68mm; max-width: 68mm; background: #f8fafc; border-right: 1.5px solid #e2e8f0; padding: 10mm 7mm; display: flex; flex-direction: column; gap: 7px; }}
    .berlin-photo {{ width: 50px; height: 50px; border-radius: 50%; overflow: hidden; border: 2px solid #0f172a; margin: 0 auto 4px auto; }}
    .berlin-photo img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .berlin-side-sec {{ margin-bottom: 5px; }}
    .berlin-side-title {{ font-size: 8pt; font-weight: 800; text-transform: uppercase; color: #0f172a; border-bottom: 1.5px solid #cbd5e1; padding-bottom: 2px; margin-bottom: 4px; letter-spacing: 0.5px; }}
    .berlin-contact-item {{ font-size: 7.5pt; color: #475569; margin-bottom: 3px; word-break: break-word; }}
    .berlin-contact-item a {{ color: #2563eb; text-decoration: none; }}
    .berlin-skill-tag {{ display: inline-block; background: #ffffff; border: 1px solid #cbd5e1; border-radius: 3px; padding: 1px 4px; font-size: 7.2pt; color: #334155; margin: 1px 1px; }}
    .berlin-main {{ flex: 1; padding: 10mm 10mm 10mm 9mm; display: flex; flex-direction: column; gap: 6px; overflow: hidden; }}
    .berlin-header {{ border-bottom: 2px solid #0f172a; padding-bottom: 6px; margin-bottom: 4px; }}
    .berlin-name {{ font-size: 18pt; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; line-height: 1; text-transform: uppercase; }}
    .berlin-title {{ font-size: 9.5pt; font-weight: 600; color: #2563eb; margin-top: 2px; }}
    .berlin-sec-title {{ font-size: 8.6pt; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 1px solid #e2e8f0; padding-bottom: 2px; margin-bottom: 4px; }}
    .berlin-summary {{ font-size: 8pt; color: #334155; line-height: 1.32; text-align: justify; margin-bottom: 4px; }}
    .berlin-exp-item {{ margin-bottom: 4px; }}
    .berlin-exp-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
    .berlin-exp-role {{ font-weight: 700; font-size: 8.5pt; color: #0f172a; }}
    .berlin-exp-date {{ font-size: 7.6pt; font-weight: 600; color: #64748b; }}
    .berlin-exp-inst {{ font-size: 7.8pt; font-style: italic; color: #475569; margin-bottom: 1.5px; }}
    .berlin-bullets {{ margin-left: 11px; font-size: 7.8pt; color: #334155; line-height: 1.25; }}
    .berlin-bullets li {{ margin-bottom: 1px; }}
    .berlin-edu-item {{ margin-bottom: 3px; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="cv-page cv-design-berlin">
    <!-- Left Sidebar -->
    <div class="berlin-sidebar">
      {photo_html}
      <div class="berlin-side-sec">
        <div class="berlin-side-title">{labels['contact']}</div>
        <div class="berlin-contact-item"><strong>Location:</strong> {city}</div>
        <div class="berlin-contact-item"><strong>Phone:</strong> {phone}</div>
        <div class="berlin-contact-item"><strong>Email:</strong> <a href="mailto:{email}">{email}</a></div>
        <div class="berlin-contact-item"><strong>LinkedIn:</strong> <a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
        {f'<div class="berlin-contact-item"><strong>GitHub:</strong> <a href="{github}">{github.replace("https://", "")}</a></div>' if github else ''}
      </div>

      <div class="berlin-side-sec">
        <div class="berlin-side-title">{labels['domains']}</div>
        <div style="font-size: 7.5pt; color: #334155; line-height: 1.3;">{domains_str}</div>
      </div>

      <div class="berlin-side-sec">
        <div class="berlin-side-title">{labels['software']}</div>
        <div style="font-size: 7.5pt; color: #334155; line-height: 1.3;">{software_str}</div>
      </div>

      {f'<div class="berlin-side-sec"><div class="berlin-side-title">{labels["hardware"]}</div><div style="font-size: 7.5pt; color: #334155; line-height: 1.3;">{hardware_str}</div></div>' if hardware_str else ''}

      <div class="berlin-side-sec">
        <div class="berlin-side-title">{labels['languages']}</div>
        <div style="font-size: 7.5pt; color: #334155; line-height: 1.3;">{langs_str}</div>
      </div>

      {f'<div class="berlin-side-sec"><div class="berlin-side-title">{labels["work_auth"]}</div><div style="font-size: 7.3pt; color: #334155; line-height: 1.25;">{work_auth}</div></div>' if work_auth else ''}
    </div>

    <!-- Right Main Column -->
    <div class="berlin-main">
      <div class="berlin-header">
        <div class="berlin-name">{full_name}</div>
        <div class="berlin-title">{title}</div>
      </div>

      {f'<div class="berlin-sec"><div class="berlin-sec-title">{labels["profile"]}</div><div class="berlin-summary">{summary}</div></div>' if summary else ''}

      <div class="berlin-sec">
        <div class="berlin-sec-title">{labels['experience']}</div>
        {exp_html}
      </div>

      <div class="berlin-sec">
        <div class="berlin-sec-title">{labels['education']}</div>
        {edu_html}
      </div>

      {f'<div class="berlin-sec"><div class="berlin-sec-title">{labels["leadership"]}</div><div style="font-size: 7.8pt; color: #334155;">{lead_str}</div></div>' if lead_str else ''}
    </div>
  </div>
</body>
</html>"""

    # DESIGN 3: STOCKHOLM TECH (Nordic Modern - Badges & Minimalist Flow)
    else:
        photo_html = f'<div class="stockholm-photo"><img src="{resolved_photo}" alt="{full_name}"></div>' if resolved_photo else ""

        exp_html = ""
        for exp in experiences[:5]:
            role = exp.get(f"role_{lang}", exp.get("role_en", ""))
            period = exp.get(f"period_{lang}", exp.get("period_en", ""))
            inst = exp.get(f"institution_{lang}", exp.get("institution_en", ""))
            bullets = exp.get("bullets", [])
            bullets_html = "".join(f"<li>{b}</li>" for b in bullets[:3])
            exp_html += f"""
            <div class="stockholm-item">
              <div class="stockholm-item-header">
                <div><span class="stockholm-role">{role}</span> <span class="stockholm-inst">&bull; {inst}</span></div>
                <div class="stockholm-date">{period}</div>
              </div>
              <ul class="stockholm-bullets">{bullets_html}</ul>
            </div>"""

        edu_html = ""
        for edu in educations[:2]:
            degree = edu.get(f"degree_{lang}", edu.get("degree_en", ""))
            period = edu.get(f"period_{lang}", edu.get("period_en", ""))
            inst = edu.get("institution", "")
            edu_html += f"""
            <div class="stockholm-item">
              <div class="stockholm-item-header">
                <div><span class="stockholm-role">{degree}</span> <span class="stockholm-inst">&bull; {inst}</span></div>
                <div class="stockholm-date">{period}</div>
              </div>
            </div>"""

        software_badges = "".join(f'<span class="nordic-pill">{s.strip()}</span>' for s in software_str.split(",") if s.strip())

        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Curriculum Vitae - {full_name}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.5pt; line-height: 1.34; color: #0f172a; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; padding: 11mm 13mm; margin: 0 auto; background: #ffffff; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }}
    .stockholm-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1.5px solid #0f172a; }}
    .stockholm-header-left {{ display: flex; align-items: center; gap: 12px; }}
    .stockholm-photo {{ width: 54px; height: 54px; border-radius: 8px; overflow: hidden; border: 1.5px solid #0f172a; }}
    .stockholm-photo img {{ width: 100%; height: 100%; object-fit: cover; display: block; }}
    .stockholm-name {{ font-size: 19pt; font-weight: 900; color: #0f172a; letter-spacing: -0.5px; line-height: 1.1; }}
    .stockholm-sub {{ font-size: 9.5pt; font-weight: 600; color: #0284c7; margin-top: 1px; }}
    .stockholm-contact {{ text-align: right; font-size: 7.8pt; color: #475569; line-height: 1.35; }}
    .stockholm-contact a {{ color: #0284c7; text-decoration: none; font-weight: 600; }}
    .stockholm-sec {{ margin-bottom: 6px; }}
    .stockholm-sec-title {{ font-size: 8.8pt; font-weight: 800; color: #0f172a; text-transform: uppercase; letter-spacing: 0.6px; display: flex; align-items: center; gap: 6px; margin-bottom: 4px; }}
    .stockholm-sec-title::after {{ content: ''; flex: 1; height: 1px; background: #e2e8f0; }}
    .stockholm-summary {{ font-size: 8.2pt; color: #334155; line-height: 1.32; text-align: justify; margin-bottom: 4px; }}
    .stockholm-item {{ margin-bottom: 4px; }}
    .stockholm-item-header {{ display: flex; justify-content: space-between; align-items: baseline; }}
    .stockholm-role {{ font-weight: 800; font-size: 8.5pt; color: #0f172a; }}
    .stockholm-inst {{ font-size: 8pt; font-weight: 500; color: #475569; }}
    .stockholm-date {{ font-size: 7.8pt; font-weight: 700; color: #0284c7; }}
    .stockholm-bullets {{ margin-left: 12px; font-size: 7.8pt; color: #334155; line-height: 1.26; }}
    .stockholm-bullets li {{ margin-bottom: 1px; }}
    .nordic-pill {{ display: inline-block; background: #f1f5f9; border: 1px solid #cbd5e1; border-radius: 4px; padding: 1px 5px; font-size: 7.4pt; font-weight: 600; color: #0f172a; margin: 1px 2px; }}
    .stockholm-skills-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 7.8pt; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .cv-page {{ width: 210mm; height: 297mm; max-height: 297mm; padding: 11mm 13mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="cv-page cv-design-stockholm">
    <div class="stockholm-header">
      <div class="stockholm-header-left">
        {photo_html}
        <div>
          <div class="stockholm-name">{full_name}</div>
          <div class="stockholm-sub">{title}</div>
        </div>
      </div>
      <div class="stockholm-contact">
        <div>{city} &bull; {phone}</div>
        <div><a href="mailto:{email}">{email}</a></div>
        <div><a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
      </div>
    </div>

    {f'<div class="stockholm-sec"><div class="stockholm-sec-title">{labels["profile"]}</div><div class="stockholm-summary">{summary}</div></div>' if summary else ''}

    <div class="stockholm-sec">
      <div class="stockholm-sec-title">{labels['experience']}</div>
      {exp_html}
    </div>

    <div class="stockholm-sec">
      <div class="stockholm-sec-title">{labels['education']}</div>
      {edu_html}
    </div>

    <div class="stockholm-sec">
      <div class="stockholm-sec-title">{labels['skills']}</div>
      <div style="margin-bottom: 2px;">{software_badges}</div>
      <div class="stockholm-skills-grid" style="margin-top: 3px;">
        <div><strong>{labels['domains']}:</strong> {domains_str}</div>
        <div><strong>{labels['languages']}:</strong> {langs_str}</div>
      </div>
      {f'<div style="font-size: 7.8pt; margin-top: 2px;"><strong>{labels["hardware"]}:</strong> {hardware_str}</div>' if hardware_str else ''}
    </div>

    {f'<div class="stockholm-sec"><div class="stockholm-sec-title">{labels["leadership"]}</div><div style="font-size: 7.8pt; color: #334155;">{lead_str}</div>{f"<div style='font-size: 7.8pt; margin-top: 2px;'><strong>{labels['work_auth']}:</strong> {work_auth}</div>" if work_auth else ""}</div>' if lead_str or work_auth else ''}
  </div>
</body>
</html>"""


def render_html_cover_letter(
    profile: Dict[str, Any],
    job_data: Dict[str, Any],
    lang: str = "en",
    design: str = "zurich",
    custom_paragraphs: Optional[List[str]] = None,
) -> str:
    """Render a complete, self-contained HTML/CSS Cover Letter in Zurich, Berlin, or Stockholm design."""
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
    hiring_manager = job_data.get("contact_person") or job_data.get("hiring_manager_contact") or job_data.get("hiring_manager", "")
    req_id = job_data.get("job_id_ref") or job_data.get("job_id", "")

    if is_de:
        today_str = datetime.now().strftime("%d. %B %Y")
        salutation = f"Sehr geehrte(r) Herr/Frau {hiring_manager}," if hiring_manager else "Sehr geehrte Damen und Herren,"
        closing = "Mit freundlichen Grüßen,"
        subject_prefix = "Bewerbung als "
    else:
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

    # DESIGN 1: ZURICH COVER LETTER
    if design.lower() == "zurich":
        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Cover Letter - {full_name} - {company}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.8pt; line-height: 1.38; color: #1e293b; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; padding: 13mm 18mm; margin: 0 auto; background: #ffffff; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }}
    .header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 2px solid #2563eb; padding-bottom: 7px; margin-bottom: 11px; }}
    .name {{ font-size: 16pt; font-weight: 800; color: #1e3a8a; letter-spacing: -0.4px; line-height: 1.1; }}
    .contact-info {{ text-align: right; font-size: 8pt; color: #475569; line-height: 1.35; }}
    .contact-info a {{ color: #2563eb; text-decoration: none; }}
    .recipient {{ margin-bottom: 9px; font-size: 8.8pt; color: #334155; line-height: 1.35; }}
    .date-line {{ margin-bottom: 9px; font-size: 8.5pt; color: #64748b; }}
    .subject-line {{ font-size: 10.2pt; font-weight: 700; color: #0f172a; margin-bottom: 9px; }}
    .salutation {{ margin-bottom: 8px; font-size: 8.8pt; font-weight: 600; }}
    .letter-para {{ margin-bottom: 7.5px; text-align: justify; color: #334155; font-size: 8.8pt; line-height: 1.36; }}
    .closing {{ margin-top: 10px; margin-bottom: 4px; font-size: 8.8pt; color: #334155; }}
    .signature-name {{ font-weight: 700; color: #0f172a; font-size: 9pt; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; padding: 13mm 18mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="letter-page letter-design-zurich">
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
      {f'<span style="font-size: 8.5pt; font-weight: normal; color: #64748b; float: right;">Ref: {req_id}</span>' if req_id else ''}
    </div>
    <div class="salutation">{salutation}</div>
    {paras_html}
    <div class="closing">{closing}</div>
    <div class="signature-name">{full_name}</div>
  </div>
</body>
</html>"""

    # DESIGN 2: BERLIN EXECUTIVE COVER LETTER
    elif design.lower() == "berlin":
        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Cover Letter - {full_name} - {company}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.8pt; line-height: 1.38; color: #1e293b; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; margin: 0 auto; background: #ffffff; display: flex; flex-direction: row; overflow: hidden; }}
    .berlin-side {{ width: 60mm; min-width: 60mm; background: #0f172a; color: #f8fafc; padding: 14mm 8mm; display: flex; flex-direction: column; justify-content: space-between; }}
    .berlin-side-name {{ font-size: 15pt; font-weight: 900; letter-spacing: -0.3px; line-height: 1.1; }}
    .berlin-side-sub {{ font-size: 8.5pt; color: #94a3b8; margin-top: 3px; font-weight: 500; }}
    .berlin-side-contact {{ font-size: 7.8pt; color: #cbd5e1; line-height: 1.4; }}
    .berlin-side-contact a {{ color: #38bdf8; text-decoration: none; }}
    .berlin-body {{ flex: 1; padding: 14mm 14mm; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }}
    .recipient {{ margin-bottom: 10px; font-size: 8.8pt; color: #334155; line-height: 1.35; }}
    .date-line {{ margin-bottom: 10px; font-size: 8.5pt; color: #64748b; text-align: right; }}
    .subject-line {{ font-size: 10.5pt; font-weight: 800; color: #0f172a; margin-bottom: 10px; border-bottom: 1.5px solid #0f172a; padding-bottom: 3px; }}
    .salutation {{ margin-bottom: 8px; font-size: 8.8pt; font-weight: 600; }}
    .letter-para {{ margin-bottom: 8px; text-align: justify; color: #334155; font-size: 8.8pt; line-height: 1.38; }}
    .closing {{ margin-top: 10px; margin-bottom: 4px; font-size: 8.8pt; color: #334155; }}
    .signature-name {{ font-weight: 700; color: #0f172a; font-size: 9pt; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="letter-page letter-design-berlin">
    <div class="berlin-side">
      <div>
        <div class="berlin-side-name">{full_name}</div>
        <div class="berlin-side-sub">Application Letter</div>
      </div>
      <div class="berlin-side-contact">
        <div><strong>Location:</strong> {city}</div>
        <div><strong>Phone:</strong> {phone}</div>
        <div><strong>Email:</strong> <a href="mailto:{email}">{email}</a></div>
        <div><strong>LinkedIn:</strong> <a href="{linkedin}">{linkedin.replace('https://', '')}</a></div>
      </div>
    </div>
    <div class="berlin-body">
      <div class="date-line">{today_str}</div>
      <div class="recipient">
        <strong>{company}</strong><br>
        {hiring_manager + '<br>' if hiring_manager else ''}
        {job_city}
      </div>
      <div class="subject-line">
        {subject_prefix}{role}
        {f'<span style="font-size: 8.5pt; font-weight: normal; color: #64748b; float: right;">Ref: {req_id}</span>' if req_id else ''}
      </div>
      <div class="salutation">{salutation}</div>
      {paras_html}
      <div class="closing">{closing}</div>
      <div class="signature-name">{full_name}</div>
    </div>
  </div>
</body>
</html>"""

    # DESIGN 3: STOCKHOLM TECH COVER LETTER
    else:
        return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
  <meta charset="UTF-8">
  <title>Cover Letter - {full_name} - {company}</title>
  <style>
    @page {{ size: A4 portrait; margin: 0; }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0 auto; background: #ffffff; font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Arial, sans-serif; font-size: 8.8pt; line-height: 1.4; color: #0f172a; -webkit-print-color-adjust: exact; print-color-adjust: exact; overflow: hidden; }}
    .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; box-sizing: border-box; padding: 13mm 18mm; margin: 0 auto; background: #ffffff; display: flex; flex-direction: column; justify-content: flex-start; overflow: hidden; }}
    .stockholm-header {{ display: flex; justify-content: space-between; align-items: flex-start; border-bottom: 1.5px solid #0f172a; padding-bottom: 8px; margin-bottom: 12px; }}
    .stockholm-name {{ font-size: 17pt; font-weight: 900; color: #0f172a; letter-spacing: -0.4px; line-height: 1.1; }}
    .stockholm-contact {{ text-align: right; font-size: 7.8pt; color: #475569; line-height: 1.35; }}
    .stockholm-contact a {{ color: #0284c7; text-decoration: none; font-weight: 600; }}
    .recipient {{ margin-bottom: 10px; font-size: 8.8pt; color: #334155; line-height: 1.35; }}
    .date-line {{ margin-bottom: 10px; font-size: 8.5pt; color: #64748b; }}
    .subject-box {{ background: #f1f5f9; border-left: 3px solid #0284c7; padding: 6px 10px; margin-bottom: 11px; font-size: 10pt; font-weight: 800; color: #0f172a; }}
    .salutation {{ margin-bottom: 8px; font-size: 8.8pt; font-weight: 600; }}
    .letter-para {{ margin-bottom: 8px; text-align: justify; color: #334155; font-size: 8.8pt; line-height: 1.38; }}
    .closing {{ margin-top: 10px; margin-bottom: 4px; font-size: 8.8pt; color: #334155; }}
    .signature-name {{ font-weight: 700; color: #0f172a; font-size: 9pt; }}
    @media print {{
      html, body {{ width: 210mm; height: 297mm; max-height: 297mm; margin: 0; padding: 0; overflow: hidden; }}
      .letter-page {{ width: 210mm; height: 297mm; max-height: 297mm; padding: 13mm 18mm; margin: 0; box-shadow: none; page-break-after: avoid; page-break-inside: avoid; overflow: hidden; }}
    }}
  </style>
</head>
<body>
  <div class="letter-page letter-design-stockholm">
    <div class="stockholm-header">
      <div class="stockholm-name">{full_name}</div>
      <div class="stockholm-contact">
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
    <div class="subject-box">
      {subject_prefix}{role}
      {f'<span style="font-size: 8.2pt; font-weight: normal; color: #64748b; float: right;">Ref: {req_id}</span>' if req_id else ''}
    </div>
    <div class="salutation">{salutation}</div>
    {paras_html}
    <div class="closing">{closing}</div>
    <div class="signature-name">{full_name}</div>
  </div>
</body>
</html>"""
