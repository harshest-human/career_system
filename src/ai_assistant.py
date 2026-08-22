"""
AI Assistant and Reasoning Engine for Career System
Synthesizes candidate profile data, job requirements, and applicant 'Why I Fit' notes
into high-converting cover letter paragraphs, bullet suggestions, and outreach pitches.
Supports Google Gemini API with robust offline NLP synthesis fallback.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional


class CareerAIAssistant:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")

    def analyze_fit_notes(
        self,
        candidate_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        user_notes: str,
        lang: str = "en",
    ) -> Dict[str, Any]:
        """Analyze applicant's fit notes and generate tailored cover letter paragraphs and bullet advice."""
        personal = candidate_profile.get("personal", {})
        cand_name = personal.get("full_name", "Applicant")
        company = job_data.get("company", "the company")
        role = job_data.get("role_title", "the position")
        skills = job_data.get("extracted_skills", [])

        # If Gemini API key is available, call Gemini
        if self.api_key:
            try:
                from google import genai
                client = genai.Client(api_key=self.api_key)
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
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt,
                )
                text_out = response.text
                # If JSON parsing succeeds return it, else fall through to synthesis
                import json
                import re
                json_match = re.search(r"\{.*\}", text_out, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
            except Exception as e:
                print(f"[AI Assistant] Gemini API call note: {e}. Using rule-based synthesis.")

        # Robust High-Quality Synthesis Fallback (100% Offline Compatible)
        if lang == "en":
            paragraphs = [
                (
                    f"I am writing to express my enthusiastic application for the {role} position at {company}. "
                    f"With my established background in {candidate_profile.get('skills', {}).get('domains', ['applied technology'])[0]} "
                    f"and proven hands-on execution, I offer a direct match for your team's current operational and growth objectives."
                ),
                (
                    f"Regarding your specific requirements: {user_notes if user_notes else f'My background spans {len(skills)} core focus areas including ' + ', '.join(skills[:4])}. "
                    f"I have consistently demonstrated the ability to bridge complex analytical workflows with reliable execution, "
                    f"ensuring measurable impact and streamlined collaboration."
                ),
                (
                    f"I am particularly drawn to {company} because of your commitment to excellence and technical innovation. "
                    f"I hold valid work authorization in Germany and am available to start in accordance with your timeline. "
                    f"I look forward to discussing how my background will support {company}'s continued success."
                ),
            ]
            bullets = [
                f"Spearhead technical deliverables aligning with {company}'s requirements in {skills[0] if skills else 'data and operations'}.",
                f"Streamline cross-functional workflows integrating {skills[1] if len(skills) > 1 else 'analytical systems'} to drive measurable efficiency.",
                f"Collaborate with project stakeholders to deliver high-quality outcomes within target timelines.",
            ]
            recs = [
                f"Highlight your direct experience with {', '.join(skills[:3]) if skills else 'core competencies'} during your introductory screening call.",
                f"Reference specific projects mentioned in your 'Why I Fit' notes during technical interviews.",
            ]
        else:
            paragraphs = [
                (
                    f"mit großem Interesse bewerbe ich mich auf die ausgeschriebene Position als {role} bei {company}. "
                    f"Mein Profil in {candidate_profile.get('skills', {}).get('domains', ['angewandter Technologie'])[0]} "
                    f"und meine praktische Erfahrung verbinden fundierte Fachkenntnisse mit lösungsorientierter Umsetzung."
                ),
                (
                    f"Zu Ihren Anforderungen: {user_notes if user_notes else f'Mein Erfahrungsspektrum deckt wesentliche Kernbereiche wie ' + ', '.join(skills[:4]) + ' ab'}. "
                    f"In meinen bisherigen Tätigkeiten habe ich komplexe Aufgabenstellungen stets strukturiert und ergebnisorientiert gelöst."
                ),
                (
                    f"Die Innovationskraft von {company} begeistert mich sehr. Gerne bringe ich meine Kompetenzen und Motivation "
                    f"gewinnbringend in Ihr Team ein. Ich freue mich auf die Gelegenheit eines persönlichen Gesprächs."
                ),
            ]
            bullets = [
                f"Erfolgreiche Leitung und Umsetzung von Projekten mit Schwerpunkt auf {skills[0] if skills else 'fachlichen Kernbereichen'}.",
                f"Strukturierte Prozessoptimierung und Datenintegration für transparente Arbeitsabläufe.",
                f"Zuverlässige Abstimmung mit Projektpartnern und Sicherstellung höchster Qualitätsstandards.",
            ]
            recs = [
                f"Betonen Sie im Erstgespräch Ihre praktische Vertrautheit mit {', '.join(skills[:3]) if skills else 'den Hauptanforderungen'}.",
                f"Verdeutlichen Sie anhand konkreter Praxisbeispiele Ihre Motivation für {company}.",
            ]

        return {
            "cover_letter_paragraphs": paragraphs,
            "suggested_bullets": bullets,
            "interview_recommendations": recs,
        }
