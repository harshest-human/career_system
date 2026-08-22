"""
Automated Web Scraping and PDF Archiving Engine
Fetches job postings from URLs, sanitizes content, extracts core text,
and generates clean archived PDFs + JSON snapshots in job_ads_auto/.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer


class JobScraper:
    def __init__(self, output_dir: Optional[Path] = None):
        self.output_dir = output_dir or Path("job_ads_auto")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "de,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }

    def sanitize_filename(self, text: str) -> str:
        """Create a filesystem-safe filename."""
        text = re.sub(r"[^\w\-_.]", "_", text)
        return re.sub(r"_+", "_", text).strip("_")

    def fetch_url(self, url: str) -> str:
        """Fetch raw HTML content with headers and timeout handling."""
        response = requests.get(url, headers=self.headers, timeout=20)
        response.raise_for_status()
        response.encoding = response.apparent_encoding or "utf-8"
        return response.text

    def extract_job_content(self, html: str, url: str) -> Dict[str, Any]:
        """Parse and sanitize job posting HTML into structured text with JSON-LD schema support."""
        soup = BeautifulSoup(html, "html.parser")

        title = ""
        company = ""
        json_ld_text = ""

        # 1. Attempt to extract structured JobPosting schema from JSON-LD
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                if script.string:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        data = next((item for item in data if isinstance(item, dict) and item.get("@type") == "JobPosting"), {})
                    if isinstance(data, dict) and data.get("@type") == "JobPosting":
                        title = data.get("title") or title
                        hiring_org = data.get("hiringOrganization")
                        if isinstance(hiring_org, dict):
                            company = hiring_org.get("name") or company
                        elif isinstance(hiring_org, str):
                            company = hiring_org
                        raw_desc = data.get("description", "")
                        if raw_desc:
                            desc_soup = BeautifulSoup(raw_desc, "html.parser")
                            json_ld_text = desc_soup.get_text(separator="\n", strip=True)
            except Exception:
                pass

        # 2. Extract H1 and OpenGraph & meta tags for title/company fallback
        h1_tag = soup.find("h1")
        if h1_tag and h1_tag.get_text(strip=True):
            title = h1_tag.get_text(strip=True)

        meta_title = soup.find("meta", property="og:title")
        raw_page_title = meta_title.get("content") if meta_title and meta_title.get("content") else (soup.title.get_text(strip=True) if soup.title else "")

        if not title and raw_page_title:
            title = raw_page_title

        # Determine company from page title patterns (e.g. "Title | Jobs bei Company GmbH", "Title at Company")
        if not company and raw_page_title:
            if "jobs bei" in raw_page_title.lower():
                company = raw_page_title.lower().split("jobs bei")[-1].strip().title()
                # Clean up original casing from raw_page_title
                match = re.search(r"jobs bei\s+(.+)$", raw_page_title, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
            elif " at " in raw_page_title.lower():
                match = re.search(r"\bat\s+(.+)$", raw_page_title, re.IGNORECASE)
                if match:
                    company = match.group(1).strip()
            elif "|" in raw_page_title:
                parts = [p.strip() for p in raw_page_title.split("|") if p.strip()]
                if len(parts) > 1:
                    company = parts[-1].replace("Jobs", "").replace("Karriere", "").replace("Careers", "").strip()

        if not company:
            meta_site = soup.find("meta", property="og:site_name")
            if meta_site and meta_site.get("content"):
                company = str(meta_site["content"]).strip()
            else:
                domain = urlparse(url).netloc.replace("www.", "")
                company = domain.split(".")[0].capitalize()

        # Clean title if it contains company suffix
        if "|" in title and len(title.split("|")) > 1:
            title = title.split("|")[0].strip()

        # 3. Strip boilerplate tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript", "svg", "button", "input"]):
            tag.decompose()

        # 4. Extract body text
        body_text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in body_text.splitlines() if len(line.strip()) > 1]
        cleaned_text = "\n".join(lines)

        full_text = f"Title: {title}\nCompany: {company}\n\n"
        if json_ld_text and len(json_ld_text) > 100:
            full_text += f"Structured Job Details:\n{json_ld_text}\n\n"
        full_text += f"Job Posting Text:\n{cleaned_text}"

        return {
            "url": url,
            "title": title or "Job Posting",
            "company": company or "Target Company",
            "scraped_at": datetime.now().isoformat(),
            "full_text": full_text.strip(),
        }

    def generate_pdf(self, job_data: Dict[str, Any], output_pdf_path: Path) -> None:
        """Generate a clean, readable PDF archive of the job posting."""
        doc = SimpleDocTemplate(
            str(output_pdf_path),
            pagesize=A4,
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "JobTitle",
            parent=styles["Heading1"],
            fontSize=16,
            leading=20,
            textColor="#1a365d",
            spaceAfter=8,
        )
        meta_style = ParagraphStyle(
            "JobMeta",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor="#4a5568",
            spaceAfter=14,
        )
        body_style = ParagraphStyle(
            "JobBody",
            parent=styles["BodyText"],
            fontSize=9.5,
            leading=13,
            textColor="#2d3748",
            spaceAfter=6,
        )

        elements = []
        # Title
        safe_title = (job_data.get("title") or "Job Posting").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        elements.append(Paragraph(f"<b>{safe_title}</b>", title_style))

        # Metadata
        company = job_data.get("company", "Unknown")
        scraped_at = job_data.get("scraped_at", "")
        url = job_data.get("url", "")
        meta_info = f"<b>Company:</b> {company} | <b>Archived:</b> {scraped_at}<br/><b>Source:</b> {url}"
        elements.append(Paragraph(meta_info, meta_style))
        elements.append(Spacer(1, 10))

        # Text paragraphs
        full_text = job_data.get("full_text", "")
        for block in full_text.split("\n\n"):
            clean_block = block.strip()
            if not clean_block:
                continue
            safe_block = clean_block.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "<br/>")
            elements.append(Paragraph(safe_block, body_style))
            elements.append(Spacer(1, 4))

        doc.build(elements)

    def scrape_url(self, url: str, custom_name: Optional[str] = None) -> Path:
        """Scrape a URL, write JSON metadata and generate an archived PDF."""
        print(f"[Scraper] Fetching {url}...")
        html = self.fetch_url(url)
        job_data = self.extract_job_content(html, url)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = custom_name or f"{job_data['company']}_{job_data['title'][:30]}"
        safe_slug = self.sanitize_filename(f"{slug}_{timestamp}")

        json_path = self.output_dir / f"{safe_slug}.json"
        pdf_path = self.output_dir / f"{safe_slug}.pdf"

        # Save JSON snapshot
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(job_data, f, indent=2, ensure_ascii=False)

        # Generate archived PDF
        self.generate_pdf(job_data, pdf_path)
        print(f"[Scraper] Successfully archived:\n  - PDF:  {pdf_path}\n  - JSON: {json_path}")
        return pdf_path


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: python scraper.py <URL> [custom_name]")
        return 1

    url = sys.argv[1]
    name = sys.argv[2] if len(sys.argv) > 2 else None
    scraper = JobScraper()
    scraper.scrape_url(url, name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
