"""
Career System - Central FastAPI Server & REST API
Manages Profiles, Job Parsing, AI Matrix Breakdown, Bilingual HTML CV/Letter Generation,
Dedicated Local Job Folders with Systematic Nomenclature: {jobposition}_{jobID}_{companyname}_{suffix}
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Body, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Initialize App and Root Paths
ROOT_DIR = Path(__file__).resolve().parent

from src.ai_assistant import CareerAIAssistant
from src.bootstrap import bootstrap_environment
from src.database import Database, get_job_prefix
from src.extractor import JobExtractor
from src.generator import LatexPipeline
from src.google_sync import GOOGLE_APPS_SCRIPT_TEMPLATE, GoogleWorkspaceSync
from src.html_templates import render_html_cover_letter, render_html_cv
from src.matcher import CandidateMatcher
from src.scraper import JobScraper
from src.tracker import NetworkTracker

# Initialize core services
bootstrap_environment()
db = Database(ROOT_DIR / "career_system.db")
extractor = JobExtractor()
matcher = CandidateMatcher()
generator = LatexPipeline()
scraper = JobScraper()
tracker = NetworkTracker()
ai_assistant = CareerAIAssistant()
google_sync = GoogleWorkspaceSync()

app = FastAPI(title="Career System AI Studio", version="3.1.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure directories exist
for folder in ["static", "templates", "job_ads_manual", "job_ads_auto", "jobs"]:
    (ROOT_DIR / folder).mkdir(parents=True, exist_ok=True)

# Mount static asset folders
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
app.mount("/jobs", StaticFiles(directory=str(ROOT_DIR / "jobs")), name="jobs")
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
    photo_src: Optional[str] = None
    photo_base64: Optional[str] = None


class OutreachRequest(BaseModel):
    candidate_id: str
    company: str
    contact_name: str
    role_title: str
    outreach_type: str = "connection"
    job_id: Optional[int] = None


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


@app.post("/api/profiles/create")
async def create_profile_endpoint(payload: Dict[str, Any] = Body(...)):
    name = payload.get("name", "New Applicant").strip()
    profile_id = payload.get("id") or re.sub(r"[^\w\-]", "_", name.lower())
    default_data = {
        "personal": {"full_name": name, "email": "", "phone": "", "city_en": "", "title_en": ""},
        "executive_summary": {"en": "", "de": ""},
        "experience": [],
        "education": [],
        "skills": {"domains": [], "software_tools": [], "hardware_instruments": [], "languages": []},
        "leadership_awards": [],
    }
    db.save_profile(profile_id, default_data)
    return {"status": "success", "profile_id": profile_id, "name": name}


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


# --- Portal Credentials & Connector Endpoints ---
@app.get("/api/portals")
async def get_portals():
    return db.get_all_portals()


@app.post("/api/portals")
async def save_portal(payload: Dict[str, Any] = Body(...)):
    portal_id = db.add_or_update_portal(payload)
    return {"status": "success", "portal_id": portal_id}


@app.delete("/api/portals/{portal_id}")
async def delete_portal(portal_id: int):
    db.delete_portal(portal_id)
    return {"status": "success"}


# --- Job Endpoints with Systematic Nomenclature ---
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

        # Copy original PDF with systematic naming: {jobposition}_{jobID}_{companyname}_description.pdf
        job_info = db.get_job(job_id)
        if job_info and job_info.get("folder_path"):
            job_folder = ROOT_DIR / job_info["folder_path"].lstrip("/")
            prefix = get_job_prefix(breakdown, job_id)
            desc_name = f"{prefix}_description.pdf"
            if job_folder.exists() and pdf_path.exists():
                shutil.copy2(pdf_path, job_folder / desc_name)

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

    # Copy PDF with systematic naming: {jobposition}_{jobID}_{companyname}_description.pdf
    job_info = db.get_job(job_id)
    if job_info and job_info.get("folder_path"):
        job_folder = ROOT_DIR / job_info["folder_path"].lstrip("/")
        prefix = get_job_prefix(breakdown, job_id)
        desc_name = f"{prefix}_description.pdf"
        if job_folder.exists() and dest_path.exists():
            shutil.copy2(dest_path, job_folder / desc_name)

    return {"status": "success", "job_id": job_id, "data": breakdown}


@app.post("/api/jobs/parse-text")
async def parse_job_text_endpoint(req: ParseTextRequest):
    gemini_key = req.gemini_api_key or os.getenv("GEMINI_API_KEY")
    breakdown = ai_assistant.extract_job_breakdown(req.raw_text, custom_api_key=gemini_key)
    breakdown["source_file"] = "manual_text_input"
    breakdown["full_text"] = req.raw_text
    job_id = db.add_or_update_job(breakdown)
    breakdown["id"] = job_id

    # Save description text file with systematic naming: {jobposition}_{jobID}_{companyname}_description.txt
    job_info = db.get_job(job_id)
    if job_info and job_info.get("folder_path"):
        job_folder = ROOT_DIR / job_info["folder_path"].lstrip("/")
        prefix = get_job_prefix(breakdown, job_id)
        desc_name = f"{prefix}_description.txt"
        if job_folder.exists():
            with open(job_folder / desc_name, "w", encoding="utf-8") as f:
                f.write(req.raw_text)

    return {"status": "success", "job_id": job_id, "data": breakdown}


@app.put("/api/jobs/{job_id}")
async def update_job_endpoint(job_id: int, payload: Dict[str, Any] = Body(...)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.update_job(job_id, payload)
    return {"status": "success", "job_id": job_id}


@app.delete("/api/jobs/{job_id}")
async def delete_job_endpoint(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete_job(job_id)

    # Clean up local folder if it exists
    if job.get("folder_path"):
        folder_path = ROOT_DIR / job["folder_path"].lstrip("/")
        if folder_path.exists():
            shutil.rmtree(folder_path, ignore_errors=True)

    return {"status": "success", "deleted_job_id": job_id}


@app.get("/api/jobs/{job_id}/files")
async def get_job_files(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    folder_rel = job.get("folder_path")
    if not folder_rel:
        return {"files": []}

    job_folder = ROOT_DIR / folder_rel.lstrip("/")
    if not job_folder.exists():
        return {"files": []}

    files = []
    for f in sorted(job_folder.iterdir(), key=lambda x: x.name):
        if f.is_file():
            size_kb = round(f.stat().st_size / 1024, 1)
            files.append({
                "name": f.name,
                "path": f"{folder_rel}/{f.name}",
                "size_kb": size_kb,
                "modified": datetime.fromtimestamp(f.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
            })

    return {"status": "success", "folder": folder_rel, "files": files}


@app.post("/api/jobs/{job_id}/open-folder")
async def open_job_folder(job_id: int):
    job = db.get_job(job_id)
    if not job or not job.get("folder_path"):
        raise HTTPException(status_code=404, detail="Job folder not found")

    folder = ROOT_DIR / job["folder_path"].lstrip("/")
    if not folder.exists():
        folder.mkdir(parents=True, exist_ok=True)

    try:
        if os.name == "nt":
            os.startfile(str(folder))
        elif sys.platform == "darwin":
            subprocess.run(["open", str(folder)])
        else:
            subprocess.run(["xdg-open", str(folder)])
        return {"status": "success", "path": str(folder)}
    except Exception as e:
        return {"status": "error", "message": str(e), "path": str(folder)}


@app.get("/api/jobs/{job_id}/export-zip")
async def export_job_zip(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    folder_rel = job.get("folder_path")
    if not folder_rel:
        raise HTTPException(status_code=404, detail="No folder found for this job")

    job_folder = ROOT_DIR / folder_rel.lstrip("/")
    if not job_folder.exists():
        raise HTTPException(status_code=404, detail="Job directory does not exist")

    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in job_folder.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(job_folder)
                zip_file.write(file_path, arcname)

    zip_buffer.seek(0)
    prefix = get_job_prefix(job, job_id)
    headers = {"Content-Disposition": f"attachment; filename={prefix}.zip"}
    return StreamingResponse(zip_buffer, media_type="application/zip", headers=headers)


@app.post("/api/jobs/import-zip")
async def import_job_zip(file: UploadFile = File(...)):
    content = await file.read()
    zip_buffer = io.BytesIO(content)

    temp_extract = ROOT_DIR / "jobs" / f"temp_{int(datetime.now().timestamp())}"
    temp_extract.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(zip_buffer, "r") as zf:
        zf.extractall(temp_extract)

    # Look for any *_meta_data.json or job_metadata.json
    meta_files = list(temp_extract.glob("*meta_data.json"))
    job_data = {}
    if meta_files:
        with open(meta_files[0], "r", encoding="utf-8") as f:
            job_data = json.load(f)

    if not job_data:
        job_data = {
            "company": "Imported Company",
            "role_title": "Imported Position",
            "location": "Location",
        }

    job_id = db.add_or_update_job(job_data)
    job_info = db.get_job(job_id)
    dest_folder = ROOT_DIR / job_info["folder_path"].lstrip("/")
    dest_folder.mkdir(parents=True, exist_ok=True)

    for item in temp_extract.iterdir():
        shutil.move(str(item), str(dest_folder / item.name))

    shutil.rmtree(temp_extract, ignore_errors=True)
    return {"status": "success", "job_id": job_id, "data": job_data}


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


# --- Photo Upload & Management Endpoints (Saves into Job Folder: {jobposition}_{jobID}_{companyname}_photo.ext) ---
@app.post("/api/jobs/{job_id}/photo")
async def upload_job_photo(job_id: int, file: UploadFile = File(...)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    ext = Path(file.filename or "photo.jpg").suffix.lower()
    if ext not in [".jpg", ".jpeg", ".png", ".webp"]:
        ext = ".jpg"

    prefix = get_job_prefix(job, job_id)
    filename = f"{prefix}_photo{ext}"

    folder_rel = job.get("folder_path") or f"/jobs/{prefix}"
    job_folder = ROOT_DIR / folder_rel.lstrip("/")
    job_folder.mkdir(parents=True, exist_ok=True)
    target_path = job_folder / filename

    content = await file.read()
    with open(target_path, "wb") as f:
        f.write(content)

    mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
    b64_str = f"data:{mime};base64,{base64.b64encode(content).decode('utf-8')}"
    web_url = f"/jobs/{job_folder.name}/{filename}"

    # Update metadata
    db.update_job(job_id, {"photo_path": web_url})

    return {
        "status": "success",
        "photo_url": web_url,
        "photo_base64": b64_str,
        "filename": filename,
    }


@app.delete("/api/jobs/{job_id}/photo")
async def delete_job_photo(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    prefix = get_job_prefix(job, job_id)
    folder_rel = job.get("folder_path") or f"/jobs/{prefix}"
    job_folder = ROOT_DIR / folder_rel.lstrip("/")

    for ext in [".jpg", ".jpeg", ".png", ".webp"]:
        p = job_folder / f"{prefix}_photo{ext}"
        if p.exists():
            try:
                p.unlink()
            except Exception:
                pass

    db.update_job(job_id, {"photo_path": ""})
    return {"status": "success", "message": "Photo removed"}


# --- HTML Document Rendering Endpoints (Saves {jobposition}_{jobID}_{companyname}_{suffix}) ---
@app.post("/api/render/html-cv")
async def render_cv_endpoint(req: CompileRequest):
    prof = db.get_profile(req.candidate_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    photo_src = req.photo_src or req.photo_base64
    job_id = req.job_data.get("id")

    # If photo_src was not explicitly passed, inspect job folder for existing photo file
    if not photo_src and job_id:
        job = db.get_job(job_id)
        if job and job.get("folder_path"):
            job_folder = ROOT_DIR / job["folder_path"].lstrip("/")
            if job_folder.exists():
                prefix = get_job_prefix(job, job_id)
                for ext in [".jpg", ".jpeg", ".png", ".webp"]:
                    p = job_folder / f"{prefix}_photo{ext}"
                    if p.exists():
                        try:
                            with open(p, "rb") as f:
                                b64 = base64.b64encode(f.read()).decode("utf-8")
                            mime = "image/png" if ext == ".png" else "image/webp" if ext == ".webp" else "image/jpeg"
                            photo_src = f"data:{mime};base64,{b64}"
                        except Exception:
                            photo_src = f"/jobs/{job_folder.name}/{p.name}"
                        break

    html_content = render_html_cv(
        profile=prof["data"],
        job_data=req.job_data,
        lang=req.lang,
        custom_summary=req.custom_summary,
        photo_src=photo_src,
    )

    # Save to job folder: {jobposition}_{jobID}_{companyname}_cv_{lang}.html
    if job_id:
        job = db.get_job(job_id)
        if job and job.get("folder_path"):
            job_folder = ROOT_DIR / job["folder_path"].lstrip("/")
            if job_folder.exists():
                prefix = get_job_prefix(job, job_id)
                filename = f"{prefix}_cv_{req.lang}.html"
                with open(job_folder / filename, "w", encoding="utf-8") as f:
                    f.write(html_content)

    return {"status": "success", "html": html_content, "photo_src": photo_src}


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

    # Save to job folder: {jobposition}_{jobID}_{companyname}_coverletter_{lang}.html
    job_id = req.job_data.get("id")
    if job_id:
        job = db.get_job(job_id)
        if job and job.get("folder_path"):
            job_folder = ROOT_DIR / job["folder_path"].lstrip("/")
            if job_folder.exists():
                prefix = get_job_prefix(job, job_id)
                filename = f"{prefix}_coverletter_{req.lang}.html"
                with open(job_folder / filename, "w", encoding="utf-8") as f:
                    f.write(html_content)

    return {"status": "success", "html": html_content}


# --- Google Drive Cloud Sync Endpoint ---
@app.post("/api/jobs/{job_id}/upload-to-drive")
async def upload_job_to_drive(job_id: int, payload: Dict[str, Any] = Body(default={})):
    job = db.get_job(job_id)
    if not job or not job.get("folder_path"):
        raise HTTPException(status_code=404, detail="Job folder not found")

    webhook_url = payload.get("webhook_url")
    if webhook_url:
        google_sync.webhook_url = webhook_url

    if not google_sync.webhook_url:
        raise HTTPException(status_code=400, detail="Google Drive Webhook URL not configured. Paste your URL in Step 1 (Account & Connectors).")

    job_folder = ROOT_DIR / job["folder_path"].lstrip("/")
    folder_name = job_folder.name
    res = google_sync.upload_job_folder_to_drive(job_folder, folder_name)
    return res


@app.get("/api/google/script-template")
async def get_google_script_template():
    return {"script": GOOGLE_APPS_SCRIPT_TEMPLATE}


@app.post("/api/google/test-sync")
async def test_google_sync(payload: Dict[str, Any] = Body(default={})):
    webhook_url = payload.get("webhook_url")
    if webhook_url:
        google_sync.webhook_url = webhook_url

    if not google_sync.webhook_url:
        raise HTTPException(status_code=400, detail="Webhook URL is empty. Please enter your Webhook URL.")

    cleaned_url = google_sync.clean_webhook_url(google_sync.webhook_url)
    test_payload = {
        "action": "test",
        "folder_name": "CareerSystem_Test_Connection",
        "files": [{"name": "test_sync.txt", "content": "Career System connection verified successfully!", "is_base64": False}],
    }
    try:
        import requests
        res = requests.post(
            cleaned_url,
            data=json.dumps(test_payload),
            headers={"Content-Type": "text/plain;charset=utf-8"},
            timeout=30,
            allow_redirects=True,
        )
        try:
            return res.json()
        except Exception:
            if "accounts.google.com" in res.text or "Sign in" in res.text:
                return {
                    "status": "error",
                    "message": "Google Authorization Error: In your Apps Script deployment, make sure 'Who has access' is set to 'Anyone' (not 'Only myself').",
                }
            return {
                "status": "error",
                "message": f"Google Script Error (HTTP {res.status_code}): {res.text[:250]}",
            }
    except Exception as e:
        return {"status": "error", "message": f"Connection Error: {str(e)}"}


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

    # Save to job folder: {jobposition}_{jobID}_{companyname}_outreach.txt
    job_id = req.job_id
    if not job_id:
        jobs = db.get_all_jobs()
        for j in jobs:
            if j.get("company", "").lower() == req.company.lower():
                job_id = j.get("id")
                break

    if job_id:
        job = db.get_job(job_id)
        if job and job.get("folder_path"):
            job_folder = ROOT_DIR / job["folder_path"].lstrip("/")
            if job_folder.exists():
                prefix = get_job_prefix(job, job_id)
                filename = f"{prefix}_outreach.txt"
                with open(job_folder / filename, "w", encoding="utf-8") as f:
                    f.write(f"Outreach Channel: {req.outreach_type}\nContact: {req.contact_name}\nRole: {req.role_title}\nCompany: {req.company}\n\n{pitch}")

    return {"status": "success", "pitch": pitch, "type": req.outreach_type}


def main():
    port = int(os.getenv("PORT", "8000"))
    print(f"\n=======================================================")
    print(f" [Career System] Local Web App Running at:")
    print(f"    http://localhost:{port} (or http://127.0.0.1:{port})")
    print(f"=======================================================")
    print(f" Nomenclature: {{jobposition}}_{{jobID}}_{{companyname}}_{{suffix}}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
