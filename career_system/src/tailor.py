"""
Local Offline Tailoring Engine for Career System
Replaces external AI APIs with deterministic, rule-based keyword matching and
bilingual template personalization for CVs, Cover Letters, and Outreach pitches.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


class OfflineTailor:
    def __init__(self):
        pass

    def tailor_summary(self, master_profile: Dict[str, Any], job_data: Dict[str, Any], lang: str = "en") -> str:
        """Generate tailored executive summary based on master profile and target job."""
        personal = master_profile.get("personal", {})
        role = job_data.get("role_title", "Specialist")
        company = job_data.get("company", "the organization")
        skills = job_data.get("extracted_skills", [])
        skills_str = ", ".join(skills[:4]) if skills else "data analysis and project execution"

        master_exec = master_profile.get("executive_summary", {}).get(lang, "")
        if master_exec and len(master_exec.strip()) > 30:
            return master_exec.strip()

        if lang.lower() == "de":
            return (
                f"Engagierter und ergebnisorientierter Fachspezialist mit fundierter Erfahrung in {skills_str}. "
                f"Nachgewiesene Erfolge in der Konzeption, Analyse und praktischen Umsetzung technischer Projekte. "
                f"Zielgerichtet, analytisch und hochmotiviert, meine Expertise als {role} bei {company} einzubringen."
            )
        else:
            return (
                f"Results-driven specialist with proven hands-on expertise in {skills_str}. "
                f"Track record of leading technical projects, optimizing workflows, and delivering actionable data insights. "
                f"Eager to leverage core technical competencies as {role} at {company}."
            )

    def tailor_cover_letter_paragraphs(
        self,
        master_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        lang: str = "en",
    ) -> List[str]:
        """Generate tailored 3-paragraph cover letter body in English or German."""
        role = job_data.get("role_title", "Position")
        company = job_data.get("company", "your company")
        skills = job_data.get("extracted_skills", [])
        skills_phrase = ", ".join(skills[:3]) if skills else "applied analytics, testing, and technical documentation"

        if lang.lower() == "de":
            p1 = (
                f"mit großem Interesse bewerbe ich mich auf die ausgeschriebene Position als {role} bei {company}. "
                f"Mein fachlicher Hintergrund und meine praktische Erfahrung in {skills_phrase} entsprechen genau dem "
                f"gesuchten Anforderungsprofil für Ihr Team."
            )
            p2 = (
                f"In meinen bisherigen Projekten und Positionen habe ich eigenverantwortlich komplexe Aufgabenstellungen gelöst, "
                f"verschiedene Fachbereiche erfolgreich vernetzt und messbare Optimierungen erzielt. "
                f"Dabei zeichnet mich eine strukturierte, lösungsorientierte und verlässliche Arbeitsweise aus."
            )
            p3 = (
                f"Ich verfüge über eine uneingeschränkte Arbeitserlaubnis in Deutschland und freue mich darauf, mich und meine "
                f"Fähigkeiten in einem persönlichen Gespräch vorzustellen."
            )
        else:
            p1 = (
                f"I am writing to express my strong interest in the {role} position at {company}. "
                f"With hands-on experience and proven execution in {skills_phrase}, I am confident in my ability to "
                f"immediately contribute to your team's operational and strategic goals."
            )
            p2 = (
                f"Throughout my professional background, I have led complex initiatives, synthesized multi-stream datasets, "
                f"and collaborated cross-functionally to achieve measurable results. I thrive in dynamic environments where "
                f"technical rigor and clear stakeholder communication are vital."
            )
            p3 = (
                f"I hold permanent work authorization in Germany and look forward to the opportunity to discuss how my "
                f"background can support {company}'s ongoing growth."
            )
        return [p1, p2, p3]

    def tailor_outreach(
        self,
        master_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        lang: str = "en",
    ) -> Dict[str, str]:
        """Generate tailored LinkedIn notes, InMail, and Cold Email in EN and DE."""
        personal = master_profile.get("personal", {})
        candidate_name = personal.get("full_name", "Applicant")
        title = personal.get(f"title_{lang}", personal.get("title_en", "Specialist"))
        role = job_data.get("role_title", "the open role")
        company = job_data.get("company", "Target Company")
        contact_name = job_data.get("contact_person") or "Hiring Team"
        phone = personal.get("phone", "")
        email = personal.get("email", "")

        if lang.lower() == "de":
            conn_note = (
                f"Hallo {contact_name}, ich verfolge die Aktivitäten von {company} mit großem Interesse. "
                f"Als {title} bringe ich fundierte Erfahrung für die Rolle als {role} mit. Ich würde mich freuen, "
                f"mich hier zu vernetzen! Beste Grüße, {candidate_name}"
            )
            if len(conn_note) > 295:
                conn_note = (
                    f"Hallo {contact_name}, ich verfolge {company} mit großem Interesse und bewerbe mich als {role}. "
                    f"Ich würde mich freuen, mich hier mit Ihnen zu vernetzen! Beste Grüße, {candidate_name}"
                )

            inmail = (
                f"Sehr geehrte(r) {contact_name},\n\n"
                f"mit großem Interesse habe ich Ihre Ausschreibung für die Position als {role} bei {company} gesehen. "
                f"Mit meinem Hintergrund als {title} bringe ich fundierte praktische Erfahrung und analytische Fähigkeiten mit, "
                f"die genau zu Ihren Anforderungen passen.\n\n"
                f"Ich habe meine Bewerbungsunterlagen bereits vorbereitet und würde mich sehr über einen kurzen Austausch freuen.\n\n"
                f"Herzliche Grüße,\n{candidate_name}"
            )

            cold_email_sub = f"Bewerbung / Initiative als {role} — {candidate_name}"
            cold_email_body = (
                f"Sehr geehrte(r) {contact_name},\n\n"
                f"ich wende mich an Sie bezüglich der Position als {role} bei {company}.\n\n"
                f"Als {title} verbinde ich fundierte Methodenkompetenz mit eigenverantwortlicher, zielstrebiger Projektarbeit. "
                f"Ich bin überzeugt, dass ich Ihr Team bei {company} schnell und wirksam unterstützen kann.\n\n"
                f"Gerne lasse ich Ihnen meinen aktuellen Lebenslauf und ein kurzes Portfolio zukommen. Über eine kurze Rückmeldung "
                f"würde ich mich sehr freuen.\n\n"
                f"Mit freundlichen Grüßen,\n{candidate_name}\n{phone} | {email}"
            )
        else:
            conn_note = (
                f"Hi {contact_name}, I'm following {company}'s great work and noticed your {role} opening. "
                f"With my background in {title}, I'd love to connect and share how I can add immediate value. Best, {candidate_name}"
            )
            if len(conn_note) > 295:
                conn_note = (
                    f"Hi {contact_name}, I saw your {role} opening at {company} and would love to connect! "
                    f"My background as {title} aligns well with your team. Best, {candidate_name}"
                )

            inmail = (
                f"Dear {contact_name},\n\n"
                f"I came across the {role} position at {company} and wanted to reach out directly. "
                f"With my background as a {title}, I have led cross-functional technical initiatives and delivered data-driven results that directly align with your requirements.\n\n"
                f"I would welcome the opportunity to connect and briefly discuss how my background can support {company}'s current milestones.\n\n"
                f"Best regards,\n{candidate_name}"
            )

            cold_email_sub = f"Application for {role} — {candidate_name}"
            cold_email_body = (
                f"Dear {contact_name},\n\n"
                f"I am writing regarding the {role} opportunity at {company}.\n\n"
                f"As a {title}, I combine strong domain expertise with rigorous analytical problem solving. "
                f"My previous track record reflects successful execution in technical projects and stakeholder collaboration, which I am eager to bring to {company}.\n\n"
                f"I would be delighted to share my CV and discuss how I can contribute to your team.\n\n"
                f"Sincerely,\n{candidate_name}\n{phone} | {email}"
            )

        return {
            "linkedin_connection": conn_note,
            "linkedin_inmail": inmail,
            "cold_email_subject": cold_email_sub,
            "cold_email_body": cold_email_body,
        }

    def tailor_application(
        self,
        master_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str = "",
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Assemble complete tailored package for CV, Cover Letter, and Outreach in EN & DE."""
        summary_en = self.tailor_summary(master_profile, job_data, lang="en")
        summary_de = self.tailor_summary(master_profile, job_data, lang="de")

        cl_en = self.tailor_cover_letter_paragraphs(master_profile, job_data, lang="en")
        cl_de = self.tailor_cover_letter_paragraphs(master_profile, job_data, lang="de")

        outreach_en = self.tailor_outreach(master_profile, job_data, lang="en")
        outreach_de = self.tailor_outreach(master_profile, job_data, lang="de")

        return {
            "tailored_profile": master_profile,
            "executive_summary": {"en": summary_en, "de": summary_de},
            "cover_letter_paragraphs": {"en": cl_en, "de": cl_de},
            "outreach": {"en": outreach_en, "de": outreach_de},
            "outreach_en": outreach_en,
            "outreach_de": outreach_de,
        }
