"""
Career System — Local Offline Career Studio & Document Engine
FastAPI application managing Jobs Hub, Master Profiles, Offline Parsing,
Direct In-Document A4 Editing (CV & Cover Letter), and Tailored Bilingual Outreach.
"""

from __future__ import annotations

import base64
import io
import json
import os
import re
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import uvicorn
from fastapi import Body, FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

ROOT_DIR = Path(__file__).resolve().parent

from src.bootstrap import bootstrap_environment
from src.database import Database, get_job_prefix
from src.extractor import JobExtractor
from src.html_templates import render_html_cover_letter, render_html_cv
from src.scraper import JobScraper
from src.tailor import OfflineTailor

# Initialize core services
bootstrap_environment()
db = Database(ROOT_DIR / "career_system.db")
extractor = JobExtractor()
scraper = JobScraper(output_dir=ROOT_DIR / "job_ads_auto")
tailor = OfflineTailor()

app = FastAPI(title="Career System Local Studio", version="4.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ensure required directories exist
for folder in ["static", "templates", "job_ads_manual", "job_ads_auto", "jobs", "profiles"]:
    (ROOT_DIR / folder).mkdir(parents=True, exist_ok=True)

# Mount static directories
app.mount("/static", StaticFiles(directory=str(ROOT_DIR / "static")), name="static")
app.mount("/jobs", StaticFiles(directory=str(ROOT_DIR / "jobs")), name="jobs")
app.mount("/job_ads_manual", StaticFiles(directory=str(ROOT_DIR / "job_ads_manual")), name="job_ads_manual")
app.mount("/job_ads_auto", StaticFiles(directory=str(ROOT_DIR / "job_ads_auto")), name="job_ads_auto")

templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))


def seed_job_application_package(job_id: int, job_data: Dict[str, Any], candidate_id: str = "default") -> None:
    """Initialize and save tailored bilingual CVs, Cover Letters, and Outreach into the job's local folder."""
    prof = db.get_profile(candidate_id) or db.get_profile("default")
    if not prof:
        return

    profile_data = prof.get("data", {})
    tailored_res = tailor.tailor_application(
        master_profile=profile_data,
        job_data=job_data,
        lang="en",
    )

    prefix = get_job_prefix(job_data, job_id)
    folder_path = ROOT_DIR / "jobs" / prefix
    folder_path.mkdir(parents=True, exist_ok=True)

    # 1. Render & save CVs (EN & DE)
    cv_en = render_html_cv(profile=profile_data, job_data=job_data, lang="en", custom_summary=tailored_res["executive_summary"]["en"])
    with open(folder_path / f"{prefix}_cv_en.html", "w", encoding="utf-8") as f:
        f.write(cv_en)

    cv_de = render_html_cv(profile=profile_data, job_data=job_data, lang="de", custom_summary=tailored_res["executive_summary"]["de"])
    with open(folder_path / f"{prefix}_cv_de.html", "w", encoding="utf-8") as f:
        f.write(cv_de)

    # 2. Render & save Cover Letters (EN & DE)
    cl_en = render_html_cover_letter(profile=profile_data, job_data=job_data, lang="en", custom_paragraphs=tailored_res["cover_letter_paragraphs"]["en"])
    with open(folder_path / f"{prefix}_coverletter_en.html", "w", encoding="utf-8") as f:
        f.write(cl_en)

    cl_de = render_html_cover_letter(profile=profile_data, job_data=job_data, lang="de", custom_paragraphs=tailored_res["cover_letter_paragraphs"]["de"])
    with open(folder_path / f"{prefix}_coverletter_de.html", "w", encoding="utf-8") as f:
        f.write(cl_de)

    # 3. Save Outreach pitches (JSON & TXT)
    outreach_data = {
        "en": tailored_res["outreach_en"],
        "de": tailored_res["outreach_de"],
        "updated_at": datetime.now().isoformat(),
    }
    with open(folder_path / f"{prefix}_outreach.json", "w", encoding="utf-8") as f:
        json.dump(outreach_data, f, indent=2, ensure_ascii=False)


# --- Multi-Page UI Routes ---

@app.get("/", response_class=HTMLResponse)
async def page_dashboard(request: Request):
    """Main Jobs Dashboard & Priority Manager."""
    jobs = db.get_all_jobs()
    profiles = db.get_all_profiles()
    return templates.TemplateResponse(request=request, name="index.html", context={"jobs": jobs, "profiles": profiles})


@app.get("/profile", response_class=HTMLResponse)
async def page_profile(request: Request, id: str = "default"):
    """Master Profile & Master Templates Editor."""
    profiles = db.get_all_profiles()
    active_profile = db.get_profile(id) or db.get_profile("default")
    return templates.TemplateResponse(request=request, name="profile.html", context={"profiles": profiles, "active_profile": active_profile, "profile_id": id})


@app.get("/job/{job_id}", response_class=HTMLResponse)
async def page_job_details(request: Request, job_id: int):
    """Job Overview, Snapshot Viewer & Extracted Details Rectifier."""
    job = db.get_job(job_id)
    if not job:
        return RedirectResponse("/")
    return templates.TemplateResponse(request=request, name="job_details.html", context={"job": job, "job_id": job_id})


@app.get("/job/{job_id}/cv", response_class=HTMLResponse)
async def page_cv_editor(request: Request, job_id: int, lang: str = "en", design: str = "zurich"):
    """Dedicated Direct In-Document A4 CV Builder with 3 European ATS Designs."""
    job = db.get_job(job_id)
    if not job:
        return RedirectResponse("/")
    
    saved_html = db.get_job_doc(job_id, "cv", lang)
    if not saved_html:
        prof = db.get_profile("default")
        profile_data = prof.get("data", {}) if prof else {}
        tailored_sum = tailor.tailor_summary(profile_data, job, lang)
        saved_html = render_html_cv(profile=profile_data, job_data=job, lang=lang, design=design, custom_summary=tailored_sum)
        db.save_job_doc(job_id, "cv", lang, saved_html)

    return templates.TemplateResponse(request=request, name="cv_editor.html", context={
        "job": job,
        "job_id": job_id,
        "lang": lang.lower(),
        "design": design.lower(),
        "doc_html": saved_html,
    })


@app.get("/job/{job_id}/coverletter", response_class=HTMLResponse)
async def page_coverletter_editor(request: Request, job_id: int, lang: str = "en", design: str = "zurich"):
    """Dedicated Direct In-Document A4 Cover Letter Builder with 3 European ATS Designs."""
    job = db.get_job(job_id)
    if not job:
        return RedirectResponse("/")
    
    saved_html = db.get_job_doc(job_id, "coverletter", lang)
    if not saved_html:
        prof = db.get_profile("default")
        profile_data = prof.get("data", {}) if prof else {}
        paras = tailor.tailor_cover_letter_paragraphs(profile_data, job, lang)
        saved_html = render_html_cover_letter(profile=profile_data, job_data=job, lang=lang, design=design, custom_paragraphs=paras)
        db.save_job_doc(job_id, "coverletter", lang, saved_html)

    return templates.TemplateResponse(request=request, name="coverletter_editor.html", context={
        "job": job,
        "job_id": job_id,
        "lang": lang.lower(),
        "design": design.lower(),
        "doc_html": saved_html,
    })


@app.get("/job/{job_id}/outreach", response_class=HTMLResponse)
async def page_outreach_editor(request: Request, job_id: int, lang: str = "en"):
    """Dedicated Outreach Messages Builder (LinkedIn Note, InMail, Cold Email)."""
    job = db.get_job(job_id)
    if not job:
        return RedirectResponse("/")
    
    outreach_data = db.get_job_outreach(job_id)
    if not outreach_data:
        prof = db.get_profile("default")
        profile_data = prof.get("data", {}) if prof else {}
        tailored_pkg = tailor.tailor_application(profile_data, job, lang="en")
        outreach_data = {
            "en": tailored_pkg["outreach_en"],
            "de": tailored_pkg["outreach_de"],
        }
        db.save_job_outreach(job_id, outreach_data)

    return templates.TemplateResponse(request=request, name="outreach_editor.html", context={
        "job": job,
        "job_id": job_id,
        "lang": lang.lower(),
        "outreach": outreach_data,
    })


# --- REST API Endpoints ---

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "mode": "100% Offline Local Studio"}


@app.get("/api/jobs")
async def get_jobs_api():
    return db.get_all_jobs()


class ReorderRequest(BaseModel):
    job_ids: List[int]


@app.post("/api/jobs/reorder")
async def reorder_jobs_api(payload: ReorderRequest):
    """Persist drag-and-drop song-style priority ordering."""
    db.reorder_jobs(payload.job_ids)
    return {"status": "success", "reordered": len(payload.job_ids)}


class ScrapeRequest(BaseModel):
    url: str
    custom_name: Optional[str] = None
    candidate_id: Optional[str] = "default"


@app.post("/api/jobs/scrape")
async def scrape_job_api(req: ScrapeRequest):
    """Scrape job URL, generate clean print-preview snapshot, parse offline, seed documents."""
    try:
        job_archive = scraper.scrape_url(req.url, req.custom_name)
        extracted = extractor.parse_job_text(job_archive.get("full_text", ""), job_archive.get("title", ""))
        extracted["source_url"] = req.url
        extracted["pdf_path"] = f"/job_ads_auto/{Path(job_archive['pdf_path']).name}"
        extracted["full_text"] = job_archive.get("full_text", "")
        
        job_id = db.add_or_update_job(extracted)
        extracted["id"] = job_id

        # Copy original snapshot PDF to dedicated job folder
        prefix = get_job_prefix(extracted, job_id)
        job_folder = ROOT_DIR / "jobs" / prefix
        job_folder.mkdir(parents=True, exist_ok=True)
        if Path(job_archive["pdf_path"]).exists():
            try:
                shutil.copy2(job_archive["pdf_path"], job_folder / f"{prefix}_description.pdf")
            except Exception:
                pass
        if Path(job_archive.get("html_path", "")).exists():
            try:
                shutil.copy2(job_archive["html_path"], job_folder / f"{prefix}_description.html")
            except Exception:
                pass

        # Seed tailored documents
        seed_job_application_package(job_id, extracted, req.candidate_id or "default")

        return {"status": "success", "job_id": job_id, "data": extracted}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ManualJobRequest(BaseModel):
    company: str
    role_title: str
    job_id_ref: Optional[str] = ""
    location: Optional[str] = "Hamburg, Germany"
    deadline: Optional[str] = ""
    employment_type: Optional[str] = "Full-time"
    contract_type: Optional[str] = "Permanent / Unbefristet"
    raw_text: Optional[str] = ""
    candidate_id: Optional[str] = "default"


@app.post("/api/jobs/manual")
async def manual_job_api(req: ManualJobRequest):
    """Manually add a job posting, run offline extraction, and seed application files."""
    extracted = extractor.parse_job_text(req.raw_text or f"{req.role_title} at {req.company}")
    extracted["company"] = req.company or extracted["company"]
    extracted["role_title"] = req.role_title or extracted["role_title"]
    extracted["job_id_ref"] = req.job_id_ref or extracted["job_id_ref"]
    extracted["location"] = req.location or extracted["location"]
    extracted["deadline"] = req.deadline or extracted["deadline"]
    extracted["employment_type"] = req.employment_type or extracted["employment_type"]
    extracted["contract_type"] = req.contract_type or extracted["contract_type"]
    extracted["full_text"] = req.raw_text

    job_id = db.add_or_update_job(extracted)
    extracted["id"] = job_id

    seed_job_application_package(job_id, extracted, req.candidate_id or "default")
    return {"status": "success", "job_id": job_id, "data": extracted}


@app.post("/api/jobs/upload")
async def upload_job_pdf_api(file: UploadFile = File(...), candidate_id: Optional[str] = Form("default")):
    """Upload a job posting PDF file, parse offline, and create job workspace."""
    dest_path = ROOT_DIR / "job_ads_manual" / file.filename
    with open(dest_path, "wb") as f:
        content = await file.read()
        f.write(content)

    extracted = extractor.process_pdf(dest_path)
    extracted["source_file"] = file.filename
    extracted["pdf_path"] = f"/job_ads_manual/{file.filename}"

    job_id = db.add_or_update_job(extracted)
    extracted["id"] = job_id

    # Copy to dedicated folder
    prefix = get_job_prefix(extracted, job_id)
    job_folder = ROOT_DIR / "jobs" / prefix
    job_folder.mkdir(parents=True, exist_ok=True)
    try:
        shutil.copy2(dest_path, job_folder / f"{prefix}_description.pdf")
    except Exception:
        pass

    seed_job_application_package(job_id, extracted, candidate_id or "default")
    return {"status": "success", "job_id": job_id, "data": extracted}


@app.get("/api/jobs/{job_id}")
async def get_job_api(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.put("/api/jobs/{job_id}")
async def update_job_api(job_id: int, payload: Dict[str, Any] = Body(...)):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.update_job(job_id, payload)
    return {"status": "success", "job_id": job_id}


@app.delete("/api/jobs/{job_id}")
async def delete_job_api(job_id: int):
    deleted = db.delete_job(job_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"status": "success", "deleted_id": job_id}


# --- Document Saving & Loading API ---

class SaveDocRequest(BaseModel):
    html_content: str


class RenderTemplateRequest(BaseModel):
    doc_type: str = "cv"  # "cv" or "coverletter"
    lang: str = "en"  # "en" or "de"
    design: str = "zurich"  # "zurich", "berlin", "stockholm"
    photo_src: Optional[str] = None
    custom_summary: Optional[str] = None
    custom_paragraphs: Optional[List[str]] = None
    candidate_id: str = "default"


@app.post("/api/jobs/{job_id}/render-template")
async def render_template_api(job_id: int, payload: RenderTemplateRequest):
    """Render and return HTML for a selected European design template."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    prof = db.get_profile(payload.candidate_id) or db.get_profile("default")
    profile_data = prof.get("data", {}) if prof else {}

    if payload.doc_type == "cv":
        summary = payload.custom_summary or tailor.tailor_summary(profile_data, job, payload.lang)
        html = render_html_cv(
            profile=profile_data,
            job_data=job,
            lang=payload.lang,
            design=payload.design,
            custom_summary=summary,
            photo_src=payload.photo_src,
        )
    else:
        paras = payload.custom_paragraphs or tailor.tailor_cover_letter_paragraphs(profile_data, job, payload.lang)
        html = render_html_cover_letter(
            profile=profile_data,
            job_data=job,
            lang=payload.lang,
            design=payload.design,
            custom_paragraphs=paras,
        )

    # Automatically save as current active version for this doc & lang
    db.save_job_doc(job_id, payload.doc_type, payload.lang, html)

    return {
        "status": "success",
        "html": html,
        "design": payload.design,
        "doc_type": payload.doc_type,
        "lang": payload.lang,
    }


@app.get("/api/jobs/{job_id}/doc/{doc_type}/{lang}")
async def get_job_doc_api(job_id: int, doc_type: str, lang: str):
    """Retrieve saved HTML document for in-place editor."""
    doc_html = db.get_job_doc(job_id, doc_type, lang)
    if not doc_html:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        prof = db.get_profile("default")
        profile_data = prof.get("data", {}) if prof else {}
        if doc_type == "cv":
            tailored_sum = tailor.tailor_summary(profile_data, job, lang)
            doc_html = render_html_cv(profile=profile_data, job_data=job, lang=lang, custom_summary=tailored_sum)
        else:
            paras = tailor.tailor_cover_letter_paragraphs(profile_data, job, lang)
            doc_html = render_html_cover_letter(profile=profile_data, job_data=job, lang=lang, custom_paragraphs=paras)
        db.save_job_doc(job_id, doc_type, lang, doc_html)

    return {"status": "success", "html": doc_html, "doc_type": doc_type, "lang": lang}


@app.post("/api/jobs/{job_id}/doc/{doc_type}/{lang}")
async def save_job_doc_api(job_id: int, doc_type: str, lang: str, payload: SaveDocRequest):
    """Directly save in-place edited HTML to local folder and database."""
    saved_path = db.save_job_doc(job_id, doc_type, lang, payload.html_content)
    return {"status": "success", "saved_path": saved_path, "updated_at": datetime.now().isoformat()}


@app.get("/api/jobs/{job_id}/outreach")
async def get_job_outreach_api(job_id: int):
    outreach = db.get_job_outreach(job_id)
    if not outreach:
        job = db.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        prof = db.get_profile("default")
        profile_data = prof.get("data", {}) if prof else {}
        tailored = tailor.tailor_application(profile_data, job, lang="en")
        outreach = {
            "en": tailored["outreach_en"],
            "de": tailored["outreach_de"],
        }
        db.save_job_outreach(job_id, outreach)
    return outreach


@app.post("/api/jobs/{job_id}/outreach")
async def save_job_outreach_api(job_id: int, payload: Dict[str, Any] = Body(...)):
    saved_path = db.save_job_outreach(job_id, payload)
    return {"status": "success", "saved_path": saved_path, "updated_at": datetime.now().isoformat()}


# --- Profiles & Master Templates API ---

@app.get("/api/profiles")
async def get_profiles_api():
    return db.get_all_profiles()


@app.get("/api/profiles/{profile_id}")
async def get_profile_details_api(profile_id: str):
    prof = db.get_profile(profile_id)
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")
    return prof


@app.post("/api/profiles/{profile_id}")
@app.put("/api/profiles/{profile_id}")
async def save_profile_api(profile_id: str, payload: Dict[str, Any] = Body(...)):
    db.save_profile(profile_id, payload)
    return {"status": "success", "profile_id": profile_id}


# --- Export Zip ---
@app.get("/api/jobs/{job_id}/export-zip")
async def export_job_zip_api(job_id: int):
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    folder_rel = job.get("folder_path")
    if not folder_rel:
        raise HTTPException(status_code=404, detail="No folder found for this job")

    job_folder = ROOT_DIR / "jobs" / folder_rel
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


    html_content = render_html_cover_letter(
        profile=profile_data,
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
