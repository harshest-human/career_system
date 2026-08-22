"""
Unified Pipeline Orchestrator for Anti-Gravity Job Application & Networking System
Ties together Web Scraping, PDF Ingestion, Analysis, Document Generation, and CRM Tracking.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

# Add workspace root to python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.extractor import JobExtractor
from src.generator import DocumentGenerator
from src.matcher import CandidateMatcher
from src.scraper import JobScraper
from src.tracker import NetworkTracker
import yaml


def get_active_profile() -> str:
    cfg = Path("config/active_user.yaml")
    if cfg.exists():
        try:
            with open(cfg, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                if data and "active_profile" in data:
                    return data["active_profile"]
        except Exception:
            pass
    return "harsh"


def cmd_scrape(args: argparse.Namespace) -> None:
    scraper = JobScraper()
    scraper.scrape_url(args.url, args.name)


def cmd_ingest(args: argparse.Namespace) -> None:
    source_pdf = Path(args.pdf_path)
    if not source_pdf.exists():
        print(f"Error: Source PDF not found: {source_pdf}")
        return

    dest_dir = Path("job_ads_manual")
    dest_dir.mkdir(exist_ok=True)
    dest_path = dest_dir / source_pdf.name
    shutil.copy(source_pdf, dest_path)
    print(f"[Ingest] Copied {source_pdf.name} to {dest_path}")

    # Immediately trigger analysis
    print("[Ingest] Running extractor...")
    extractor = JobExtractor()
    parsed = extractor.process_pdf(dest_path)
    print(f"  Company: {parsed['company']}")
    print(f"  Role:    {parsed['role_title']}")
    print(f"  Skills:  {', '.join(parsed['extracted_skills'])}")


def cmd_analyze(args: argparse.Namespace) -> None:
    extractor = JobExtractor()
    matcher = CandidateMatcher()

    jobs = []
    for folder in [Path("job_ads_manual"), Path("job_ads_auto")]:
        if folder.exists():
            jobs.extend(extractor.process_directory(folder))

    # Also include existing job folders in root if they have PDFs
    for root_item in Path(".").iterdir():
        if root_item.is_dir() and root_item.name not in [".venv", "build", "tmp", "job_ads_manual", "job_ads_auto", "latex_generator", "network_tracker", "outputs", "profiles", "config", "src", ".git"]:
            jobs.extend(extractor.process_directory(root_item))

    if not jobs:
        print("[Analyze] No job ad PDFs found in manual or auto directories.")
        return

    print(f"[Analyze] Extracted {len(jobs)} job postings.")
    matrix_path = matcher.generate_matrix(jobs)
    print(f"[Analyze] Updated database at {matrix_path}")


def cmd_generate(args: argparse.Namespace) -> None:
    generator = DocumentGenerator()
    skills_list = [s.strip() for s in args.skills.split(",")] if args.skills else []

    job_data = {
        "company": args.company,
        "role_title": args.role,
        "location": args.location or "Hamburg, Germany",
        "hiring_manager": args.hiring_manager or "",
        "req_id": args.req_id or "",
        "extracted_skills": skills_list,
    }

    generator.generate_documents(
        candidate_id=args.profile,
        job_data=job_data,
        lang=args.lang,
    )


def cmd_outreach(args: argparse.Namespace) -> None:
    tracker = NetworkTracker()
    tpl_map = {
        "connection": "linkedin_connection.txt",
        "inmail": "linkedin_inmail.txt",
        "email": "cold_email.txt",
        "followup": "followup.txt",
    }
    tpl_file = tpl_map.get(args.type, "linkedin_connection.txt")
    pitch = tracker.generate_pitch(
        candidate_id=args.profile,
        company=args.company,
        contact_name=args.contact,
        role_title=args.role or "Open Position",
        template_name=tpl_file,
    )

    print("\n" + "=" * 60)
    print(f"OUTREACH MESSAGE ({args.type.upper()}) for {args.contact} @ {args.company}")
    print("=" * 60)
    print(pitch)
    print("=" * 60 + "\n")

    if args.log:
        tracker.log_interaction(
            candidate_id=args.profile,
            company=args.company,
            contact_name=args.contact,
            channel="LinkedIn" if "linkedin" in tpl_file else "Email",
            message_type=args.type,
            status="Drafted / Ready",
            notes=f"Generated {args.type} outreach pitch.",
        )


def cmd_status(args: argparse.Namespace) -> None:
    print("\n=== Anti-Gravity Job Application Pipeline Status ===")
    profiles = [p.name for p in Path("profiles").iterdir() if p.is_dir()]
    print(f"Active Candidate Profiles: {', '.join(profiles)}")

    manual_ads = list(Path("job_ads_manual").glob("*.pdf")) if Path("job_ads_manual").exists() else []
    auto_ads = list(Path("job_ads_auto").glob("*.pdf")) if Path("job_ads_auto").exists() else []
    print(f"Job Ads Stored: {len(manual_ads)} manual, {len(auto_ads)} auto-scraped")

    contacts_df = NetworkTracker().load_contacts()
    print(f"Network Contacts Tracked: {len(contacts_df)}")

    print("\nOutputs Available:")
    for prof in profiles:
        prof_out = Path("outputs") / prof
        if prof_out.exists():
            jobs = [d.name for d in prof_out.iterdir() if d.is_dir()]
            print(f"  - {prof}: {len(jobs)} tailored application packages")
            for j in jobs:
                print(f"      * {j}")
    print("=====================================================\n")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Anti-Gravity Job Application & Networking Pipeline Orchestrator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Scrape
    p_scrape = subparsers.add_parser("scrape", help="Scrape a job ad URL and archive PDF")
    p_scrape.add_argument("--url", required=True, help="Job posting URL")
    p_scrape.add_argument("--name", default=None, help="Custom slug name")
    p_scrape.set_defaults(func=cmd_scrape)

    # Ingest
    p_ingest = subparsers.add_parser("ingest", help="Ingest a manual PDF job ad")
    p_ingest.add_argument("--pdf-path", required=True, help="Path to PDF")
    p_ingest.set_defaults(func=cmd_ingest)

    # Analyze
    p_analyze = subparsers.add_parser("analyze", help="Extract metadata and build matrix")
    p_analyze.set_defaults(func=cmd_analyze)

    # Generate
    p_gen = subparsers.add_parser("generate", help="Generate tailored CV & Cover Letter PDFs")
    p_gen.add_argument("--profile", default=get_active_profile(), help="Candidate profile ID (harsh, wife, ayush)")
    p_gen.add_argument("--company", required=True, help="Target company name")
    p_gen.add_argument("--role", required=True, help="Target role title")
    p_gen.add_argument("--location", default="Hamburg, Germany", help="Job location")
    p_gen.add_argument("--hiring-manager", default="", help="Hiring manager or recruiter name")
    p_gen.add_argument("--req-id", default="", help="Job requisition ID")
    p_gen.add_argument("--skills", default="", help="Comma-separated required skills")
    p_gen.add_argument("--lang", default="en", choices=["en", "de"], help="Language (en or de)")
    p_gen.set_defaults(func=cmd_generate)

    # Outreach
    p_out = subparsers.add_parser("outreach", help="Generate networking & CRM message")
    p_out.add_argument("--profile", default=get_active_profile(), help="Candidate profile ID")
    p_out.add_argument("--company", required=True, help="Company name")
    p_out.add_argument("--contact", default="Hiring Team", help="Contact person name")
    p_out.add_argument("--role", default="", help="Role title")
    p_out.add_argument("--type", default="connection", choices=["connection", "inmail", "email", "followup"])
    p_out.add_argument("--log", action="store_true", help="Log to outreach history")
    p_out.set_defaults(func=cmd_outreach)

    # Status
    p_status = subparsers.add_parser("status", help="Show system status and summary")
    p_status.set_defaults(func=cmd_status)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return 0

    args.func(args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
