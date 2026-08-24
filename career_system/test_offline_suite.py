"""
Comprehensive Verification Suite for Career System 100% Offline Local Studio
"""

import json
from pathlib import Path
from fastapi.testclient import TestClient

import app

client = TestClient(app.app)

def test_system():
    print("\n=======================================================")
    print(" [1/6] Testing Health & Offline Mode...")
    print("=======================================================")
    res = client.get("/api/health")
    assert res.status_code == 200
    print("Health response:", res.json())

    print("\n=======================================================")
    print(" [2/6] Testing Profile & Master Templates API...")
    print("=======================================================")
    res = client.get("/api/profiles/default")
    assert res.status_code == 200
    prof = res.json()
    print("Master profile loaded for:", prof.get("data", {}).get("personal", {}).get("full_name"))

    print("\n=======================================================")
    print(" [3/6] Testing Offline Job Parsing & Document Seeding...")
    print("=======================================================")
    sample_text = """
    Agrartechnologie Nord GmbH
    Position: Junior Data Scientist (m/w/d)
    Referenznummer: AGRI-2026-882
    Standort: Hamburg
    Arbeitsmodell: Hybrid (2 Tage Homeoffice)
    Anstellungsart: Vollzeit (Unbefristet)
    Bewerbungsfrist: 30.11.2026
    Gehaltsspanne: 55.000 € - 65.000 €
    Kontakt: Dr. Martin Schmidt, Email: karriere@agrar-nord.de, Tel: +49 40 987654321

    Ihre Aufgaben:
    - Auswertung von Sensor- und FTIR-Messdaten
    - Entwicklung von Python-Pipelines zur Datenanalyse
    - Erstellung von Berichten und Präsentationen für Projektpartner

    Ihr Profil:
    - Studium der Agrarwissenschaften, Informatik oder Bio-Data Science
    - Fundierte Kenntnisse in Python, R und statistischer Versuchsplanung
    - Teamfähigkeit und strukturierte Arbeitsweise
    """

    res = client.post("/api/jobs/manual", json={
        "company": "Agrartechnologie Nord GmbH",
        "role_title": "Junior Data Scientist (m/w/d)",
        "location": "Hamburg",
        "raw_text": sample_text,
        "candidate_id": "default"
    })
    assert res.status_code == 200
    job_res = res.json()
    job_id = job_res["job_id"]
    print(f"Created Job #{job_id}: {job_res['data']['role_title']} at {job_res['data']['company']}")
    print("Extracted Skills:", job_res["data"]["extracted_skills"])
    print("Extracted Ref:", job_res["data"]["job_id_ref"])
    print("Extracted Contact:", job_res["data"]["contact_person"], "|", job_res["data"]["contact_email"])

    print("\n=======================================================")
    print(" [4/6] Verifying Multi-Page Direct HTML Document Views...")
    print("=======================================================")
    # CV Editor EN
    res = client.get(f"/job/{job_id}/cv?lang=en")
    assert res.status_code == 200
    assert "Curriculum Vitae" in res.text
    print(f" [PASS] GET /job/{job_id}/cv?lang=en returned 200 OK")

    # Cover Letter DE
    res = client.get(f"/job/{job_id}/coverletter?lang=de")
    assert res.status_code == 200
    assert "Cover Letter" in res.text or "Bewerbung" in res.text
    print(f" [PASS] GET /job/{job_id}/coverletter?lang=de returned 200 OK")

    # Outreach Page
    res = client.get(f"/job/{job_id}/outreach?lang=en")
    assert res.status_code == 200
    assert "LinkedIn Connection Request" in res.text
    print(f" [PASS] GET /job/{job_id}/outreach?lang=en returned 200 OK")

    # Job Details Page
    res = client.get(f"/job/{job_id}")
    assert res.status_code == 200
    assert "Job Workspace" in res.text
    print(f" [PASS] GET /job/{job_id} returned 200 OK")

    print("\n=======================================================")
    print(" [5/6] Testing Direct In-Place Document Auto-Saving...")
    print("=======================================================")
    custom_cv_html = "<div class='cv-page'><h1>Custom Edited CV Content</h1></div>"
    res = client.post(f"/api/jobs/{job_id}/doc/cv/en", json={"html_content": custom_cv_html})
    assert res.status_code == 200
    print("Saved CV result:", res.json())

    # Retrieve saved document
    res = client.get(f"/api/jobs/{job_id}/doc/cv/en")
    assert res.status_code == 200
    assert "Custom Edited CV Content" in res.json()["html"]
    print(" [PASS] Successfully retrieved customized CV from local job folder!")

    print("\n=======================================================")
    print(" [6/6] Testing Drag-and-Drop Priority Reordering...")
    print("=======================================================")
    # Get all jobs
    res = client.get("/api/jobs")
    assert res.status_code == 200
    all_jobs = res.json()
    job_ids = [j["id"] for j in all_jobs]
    reversed_ids = list(reversed(job_ids))
    
    # Reorder
    res = client.post("/api/jobs/reorder", json={"job_ids": reversed_ids})
    assert res.status_code == 200
    print("Reorder result:", res.json())

    # Verify order in DB
    res = client.get("/api/jobs")
    new_jobs = res.json()
    assert [j["id"] for j in new_jobs] == reversed_ids
    print(f" [PASS] Jobs successfully reordered by priority: {reversed_ids}")

    print("\n=======================================================")
    print(" ALL 6 TEST STAGES PASSED PERFECTLY!")
    print("=======================================================\n")

if __name__ == "__main__":
    test_system()

