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


class JobStatusUpdate(BaseModel):
    status: str


class AnalyzeRequest(BaseModel):
    candidate_id: str
    job_id: Optional[int] = None
    raw_text: Optional[str] = None


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
        extracted = extractor.process_pdf(pdf_path)
        extracted["source_url"] = req.url
        extracted["source_file"] = pdf_path.name
        job_id = db.add_or_update_job(extracted)
        return {"status": "success", "job_id": job_id, "data": extracted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/jobs/upload")
async def upload_job(file: UploadFile = File(...)):
    dest_path = ROOT_DIR / "job_ads_manual" / file.filename
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    extracted = extractor.process_pdf(dest_path)
    extracted["source_file"] = file.filename
    job_id = db.add_or_update_job(extracted)
    return {"status": "success", "job_id": job_id, "data": extracted}


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
        job_data = extractor.parse_job_text(req.raw_text, "custom_input.txt")

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
    )

    cv_pdf_rel = str(doc_res["cv_pdf"].relative_to(ROOT_DIR)).replace("\\", "/") if doc_res.get("cv_pdf") else None
    letter_pdf_rel = str(doc_res["letter_pdf"].relative_to(ROOT_DIR)).replace("\\", "/") if doc_res.get("letter_pdf") else None

    return {
        "status": "success",
        "cv_pdf": f"/{cv_pdf_rel}" if cv_pdf_rel else None,
        "letter_pdf": f"/{letter_pdf_rel}" if letter_pdf_rel else None,
    }


# --- Outreach & CRM Endpoints ---
@app.get("/api/contacts")
async def get_contacts():
    return db.get_all_contacts()


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
