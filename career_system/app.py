"""
Career System Local Web Application (FastAPI Server)
Provides REST API and visual browser dashboard for Profile Management,
Job Ingestion, AI Gap Analysis, Interactive LaTeX CV/Cover Letter Studio, and Networking CRM.
"""

from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add workspace root to sys.path
ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

from src.ai_assistant import CareerAIAssistant
from src.bootstrap import check_and_bootstrap_environment
from src.database import Database
from src.extractor import JobExtractor
from src.generator import DocumentGenerator
from src.google_sync import GoogleWorkspaceSync, GOOGLE_APPS_SCRIPT_TEMPLATE
from src.html_templates import render_html_cover_letter, render_html_cv
from src.matcher import CandidateMatcher
from src.scraper import JobScraper
from src.tracker import NetworkTracker

# Initialize dependencies & DB
check_and_bootstrap_environment()
db = Database()
ai_assistant = CareerAIAssistant()
extractor = JobExtractor()
matcher = CandidateMatcher()
generator = DocumentGenerator()
scraper = JobScraper()
tracker = NetworkTracker()
google_sync = GoogleWorkspaceSync()

app = FastAPI(title="Anti-Gravity Career System", version="2.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
for folder in ["static", "templates", "job_ads_manual", "job_ads_auto", "outputs"]:
    Path(folder).mkdir(parents=True, exist_ok=True)

# Mount static asset folders
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
app.mount("/outputs", StaticFiles(directory=str(ROOT_DIR / "outputs")), name="outputs")
app.mount("/job_ads_manual", StaticFiles(directory=str(ROOT_DIR / "job_ads_manual")), name="job_ads_manual")
app.mount("/job_ads_auto", StaticFiles(directory=str(ROOT_DIR / "job_ads_auto")), name="job_ads_auto")


# --- Pydantic Request Models ---
class ScrapeRequest(BaseModel):
    url: str
    custom_name: Optional[str] = None
    gemini_api_key: Optional[str] = None


class ParseTextRequest(BaseModel):
    raw_text: str
    gemini_api_key: Optional[str] = None


class JobStatusUpdate(BaseModel):
    status: str


class AnalyzeRequest(BaseModel):
    candidate_id: str
    job_id: Optional[int] = None
    raw_text: Optional[str] = None
    gemini_api_key: Optional[str] = None


class SuggestRequest(BaseModel):
    candidate_id: str
    job_data: Dict[str, Any]
    user_notes: str
    lang: str = "en"
    gemini_api_key: Optional[str] = None


class CompileRequest(BaseModel):
    candidate_id: str
    job_data: Dict[str, Any]
    lang: str = "en"
    custom_summary: Optional[str] = None
    custom_bullets: Optional[List[str]] = None
    custom_letter_paragraphs: Optional[List[str]] = None


class OutreachRequest(BaseModel):
    candidate_id: str
    company: str
    contact_name: str
    role_title: str
    outreach_type: str = "connection"


# --- HTML Frontend Route ---
@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_file = ROOT_DIR / "templates" / "index.html"
    if not index_file.exists():
        return "<h1>Career System UI is being configured...</h1>"
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()


# --- Health Endpoint ---
@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "Career System Server is running"}


# --- Profile Endpoints ---
@app.get("/api/profiles")
async def get_profiles():
    return db.get_all_profiles()


@app.get("/api/profiles/{profile_id}")
async def get_profile_details(profile_id: str):
    prof = db.get_profile(profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    return prof


@app.post("/api/profiles/{profile_id}")
@app.put("/api/profiles/{profile_id}")
async def save_profile(profile_id: str, payload: Dict[str, Any] = Body(...)):
    db.save_profile(profile_id, payload)
    return {"status": "success", "profile_id": profile_id}


# --- Job Endpoints ---
@app.get("/api/jobs")
async def get_jobs():
    return db.get_all_jobs()


@app.post("/api/jobs/scrape")
async def scrape_job(req: ScrapeRequest):
    try:
        pdf_path = scraper.scrape_url(req.url, req.custom_name)
        raw_text = extractor.extract_text_from_pdf(pdf_path)
        gemini_key = req.gemini_api_key or os.getenv("GEMINI_API_KEY")
        breakdown = ai_assistant.extract_job_breakdown(raw_text, custom_api_key=gemini_key)
        breakdown["source_url"] = req.url
        breakdown["source_file"] = pdf_path.name
        breakdown["pdf_path"] = f"/job_ads_auto/{pdf_path.name}"
        breakdown["full_text"] = raw_text
        job_id = db.add_or_update_job(breakdown)
        breakdown["id"] = job_id
        return {"status": "success", "job_id": job_id, "data": breakdown}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/upload")
async def upload_job(
    file: UploadFile = File(...),
    gemini_api_key: Optional[str] = None,
):
    dest_path = ROOT_DIR / "job_ads_manual" / file.filename
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    raw_text = extractor.extract_text_from_pdf(dest_path)
    breakdown = ai_assistant.extract_job_breakdown(raw_text, custom_api_key=gemini_api_key)
    breakdown["source_file"] = file.filename
    breakdown["pdf_path"] = f"/job_ads_manual/{file.filename}"
    breakdown["full_text"] = raw_text
    job_id = db.add_or_update_job(breakdown)
    breakdown["id"] = job_id
    return {"status": "success", "job_id": job_id, "data": breakdown}


@app.post("/api/jobs/parse-text")
async def parse_job_text_endpoint(req: ParseTextRequest):
    gemini_key = req.gemini_api_key or os.getenv("GEMINI_API_KEY")
    breakdown = ai_assistant.extract_job_breakdown(req.raw_text, custom_api_key=gemini_key)
    breakdown["source_file"] = "manual_text_input"
    breakdown["full_text"] = req.raw_text
    job_id = db.add_or_update_job(breakdown)
    breakdown["id"] = job_id
    return {"status": "success", "job_id": job_id, "data": breakdown}


@app.put("/api/jobs/{job_id}/status")
async def update_job_status(job_id: int, req: JobStatusUpdate):
    db.update_job_status(job_id, req.status)
    return {"status": "success"}


# --- Analysis & AI Suggestion Endpoints ---
@app.post("/api/analyze")
async def analyze_match(req: AnalyzeRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    job_data = None
    if req.job_id:
        job_data = db.get_job(req.job_id)
    elif req.raw_text:
        gemini_key = req.gemini_api_key or os.getenv("GEMINI_API_KEY")
        job_data = ai_assistant.extract_job_breakdown(req.raw_text, custom_api_key=gemini_key)
        job_data["source_file"] = "manual_text_input"
        job_id = db.add_or_update_job(job_data)
        job_data["id"] = job_id

    if not job_data:
        raise HTTPException(status_code=400, detail="No job data provided")

    match_result = matcher.compute_match(req.candidate_id, job_data)
    return {
        "job": job_data,
        "match_result": match_result,
        "candidate": prof["data"]["personal"]["full_name"],
    }


@app.post("/api/ai/suggest")
async def ai_suggest(req: SuggestRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    if req.gemini_api_key:
        ai_assistant.api_key = req.gemini_api_key

    result = ai_assistant.analyze_fit_notes(
        candidate_profile=prof["data"],
        job_data=req.job_data,
        user_notes=req.user_notes,
        lang=req.lang,
    )
    return result


# --- Dynamic LaTeX Compilation & PDF Streaming ---
@app.post("/api/compile")
async def compile_documents(req: CompileRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    profile_data = prof["data"]
    if req.custom_summary:
        profile_data.setdefault("executive_summary", {})[req.lang] = req.custom_summary

    # Prepare document generation
    doc_res = generator.generate_documents(
        candidate_id=req.candidate_id,
        job_data=req.job_data,
        lang=req.lang,
        custom_summary=req.custom_summary,
        custom_letter_paragraphs=req.custom_letter_paragraphs,
    )

    def to_web_path(path_obj: Optional[Path]) -> Optional[str]:
        if not path_obj:
            return None
        try:
            rel = path_obj.resolve().relative_to(ROOT_DIR.resolve())
            return f"/{str(rel).replace('\\', '/')}"
        except Exception:
            clean = str(path_obj).replace("\\", "/").lstrip("/")
            return f"/{clean}"

    cv_pdf_rel = to_web_path(doc_res.get("cv_pdf"))
    letter_pdf_rel = to_web_path(doc_res.get("letter_pdf"))

    return {
        "status": "success",
        "cv_pdf": cv_pdf_rel,
        "letter_pdf": letter_pdf_rel,
    }


# --- HTML Document Rendering Endpoints (No LaTeX Required) ---
@app.post("/api/render/html-cv")
async def render_cv_endpoint(req: CompileRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    html_content = render_html_cv(
        profile=prof["data"],
        job_data=req.job_data,
        lang=req.lang,
        custom_summary=req.custom_summary,
    )
    return {"status": "success", "html": html_content}


@app.post("/api/render/html-letter")
async def render_letter_endpoint(req: CompileRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    html_content = render_html_cover_letter(
        profile=prof["data"],
        job_data=req.job_data,
        lang=req.lang,
        custom_paragraphs=req.custom_letter_paragraphs,
    )
    return {"status": "success", "html": html_content}


# --- Google Workspace & Drive Sync Endpoints ---
@app.post("/api/export/google-docs")
async def export_to_google_docs(payload: Dict[str, Any] = Body(...)):
    candidate_id = payload.get("candidate_id", "harsh")
    prof = db.get_profile(candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    webhook_url = payload.get("webhook_url")
    if webhook_url:
        google_sync.webhook_url = webhook_url

    formatted_text = google_sync.format_cv_for_google_docs(prof["data"], lang=payload.get("lang", "en"))
    
    # If webhook configured, create doc in Drive
    if google_sync.webhook_url:
        sync_res = google_sync.create_google_doc(
            title=f"CV - {prof['name']} - {payload.get('company', 'Application')}",
            content=formatted_text,
        )
        return {"status": "success", "doc_url": sync_res.get("doc_url"), "text": formatted_text}

    return {"status": "success", "text": formatted_text}


@app.post("/api/export/google-sheets")
async def export_to_google_sheets(payload: Dict[str, Any] = Body(...)):
    webhook_url = payload.get("webhook_url")
    if webhook_url:
        google_sync.webhook_url = webhook_url

    job_data = payload.get("job_data", {})
    candidate_name = payload.get("candidate_name", "Applicant")
    fit_score = payload.get("fit_score", "")

    sync_res = google_sync.sync_job_to_sheet(job_data, candidate_name, fit_score)
    return sync_res


@app.get("/api/google/script-template")
async def get_google_script_template():
    return {"script": GOOGLE_APPS_SCRIPT_TEMPLATE}


@app.post("/api/contacts")
async def create_contact(payload: Dict[str, Any] = Body(...)):
    contact_id = db.add_contact(payload)
    return {"status": "success", "contact_id": contact_id}


@app.post("/api/outreach/generate")
async def generate_outreach_pitch(req: OutreachRequest):
    tpl_map = {
        "connection": "linkedin_connection.txt",
        "inmail": "linkedin_inmail.txt",
        "email": "cold_email.txt",
        "followup": "followup.txt",
    }
    tpl_file = tpl_map.get(req.outreach_type, "linkedin_connection.txt")
    pitch = tracker.generate_pitch(
        candidate_id=req.candidate_id,
        company=req.company,
        contact_name=req.contact_name,
        role_title=req.role_title,
        template_name=tpl_file,
    )
    return {"status": "success", "pitch": pitch, "type": req.outreach_type}


def main():
    port = int(os.getenv("PORT", "8000"))
    print(f"\n=======================================================")
    print(f" [Career System] Local Web App Running at:")
    print(f"    http://localhost:{port} (or http://127.0.0.1:{port})")
    print(f"=======================================================\n")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
