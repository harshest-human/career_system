# Anti-Gravity: Automated Multi-Candidate Job Application & Networking Pipeline

A unified, multi-candidate career intelligence and application automation pipeline designed for **Anti-Gravity**. Built for **Harsh Sahu**, his **wife**, and his **brother Ayush**, enabling each person to run their own tailored AI Career Copilot, analyze job opportunities, generate ATS-optimized LaTeX CVs & Cover Letters, and track hiring manager outreach.

---

## 🌟 Key Features

1. **Multi-Candidate AI Copilot**:
   - Dedicated master profile repositories for each candidate under `profiles/<candidate>/`.
   - Anti-Gravity automatically grounds all AI suggestions, bullets, and letters in the active candidate's background.
2. **Automated Web Scraping & Archiving (`/job_ads_auto/`)**:
   - Ingests job posting URLs, strips web bloat, extracts clean markdown/text, and generates archived PDFs.
3. **Intelligent Parsing & Tabular Matrix (`/job_analysis/`)**:
   - Ingests manual and auto-scraped PDFs using `pdfplumber` and NLP/Regex heuristics.
   - Computes Candidate Match Fit Scores (%) and outputs structured comparison spreadsheets (`job_matrix.xlsx` & `job_matrix.csv`).
4. **Dynamic Jinja2-LaTeX Document Generator (`/outputs/`)**:
   - Tailors resume bullets and cover letter paragraphs based on role keywords.
   - Multi-pass `XeLaTeX` compilation for pixel-perfect English and German PDFs.
5. **Lightweight Networking & Outreach CRM (`/network_tracker/`)**:
   - Master recruiter/hiring manager database (`contacts.csv`).
   - Generates personalized LinkedIn connection notes, InMails, cold emails, and follow-ups.

---

## 📂 Workspace Structure

```
d:/Job Application/
├── .antigravity/                          # Anti-Gravity AI Copilot rules & instructions
│   └── rules/
│       └── career-copilot.md              # System prompt grounding the AI in candidate data
├── config/
│   ├── settings.yaml                      # Global pipeline configuration
│   └── active_user.yaml                   # Active candidate on this machine (harsh | wife | ayush)
├── profiles/                              # Multi-candidate profile storage
│   ├── harsh/
│   │   ├── profile.yaml                   # Harsh's master bio, degrees, research, tech stack
│   │   ├── bullets_en.yaml                # Categorized achievement bullets (EN)
│   │   └── bullets_de.yaml                # Categorized achievement bullets (DE)
│   ├── wife/
│   │   ├── profile.yaml                   # Master bio template
│   │   ├── bullets_en.yaml
│   │   └── bullets_de.yaml
│   └── ayush/
│       ├── profile.yaml                   # Master bio template
│       ├── bullets_en.yaml
│       └── bullets_de.yaml
├── job_ads_manual/                        # Drop manually downloaded job ad PDFs here
├── job_ads_auto/                          # Scraped job postings (PDFs & JSON metadata)
├── job_analysis/                          # Extracted job spreadsheets (job_matrix.xlsx / .csv)
├── latex_generator/                       # Core LaTeX templates & style packages
│   └── templates/                         # Jinja2 LaTeX templates (cv_en, cv_de, letter_en, letter_de)
├── network_tracker/                       # Lightweight CRM: contacts & message templates
│   ├── templates/                         # LinkedIn, InMail, Email, and Follow-up templates
│   ├── contacts.csv                       # Master contact database
│   └── outreach_log.yaml                  # Interaction history
├── outputs/                               # Final generated PDFs organized by candidate
│   ├── harsh/
│   ├── wife/
│   └── ayush/
├── src/                                   # Pipeline engine modules
│   ├── scraper.py                         # Web scraping & PDF archiving
│   ├── extractor.py                       # PDF text & metadata parsing
│   ├── matcher.py                         # Candidate scoring & matrix builder
│   ├── generator.py                       # Jinja2-LaTeX dynamic document engine
│   └── tracker.py                         # CRM & message generator
├── setup.ps1                              # Automated setup script (Windows)
├── setup.sh                               # Automated setup script (macOS/Linux)
└── pipeline.py                            # Unified CLI orchestrator
```

---

## 🚀 How to Share & Run via GitHub (Multi-Laptop Setup)

### Step 1: Push This Workspace to GitHub

1. Open a terminal in this workspace folder (`d:/Job Application`):
   ```bash
   git init
   git add .
   git commit -m "Initial commit: Multi-candidate Job Application Pipeline"
   ```
2. Create a new **Private Repository** on your GitHub account (e.g. `career-pipeline`).
3. Link and push your repository:
   ```bash
   git remote add origin https://github.com/<your-username>/<repo-name>.git
   git branch -M main
   git push -u origin main
   ```
4. Invite your wife and brother Ayush as collaborators on GitHub (under **Settings > Collaborators**).

---

### Step 2: Running on Personal Laptops in Anti-Gravity

When your wife or Ayush opens the repository on their laptop:

1. **Clone the repository**:
   ```bash
   git clone https://github.com/<your-username>/<repo-name>.git
   cd <repo-name>
   ```
2. **Run the One-Click Setup Script**:
   - On **Windows**:
     ```powershell
     .\setup.ps1
     ```
   - On **macOS / Linux**:
     ```bash
     chmod +x setup.sh && ./setup.sh
     ```
   *(This automatically installs `uv`, creates the `.venv` environment, installs dependencies, and checks LaTeX).*

3. **Set the Active Profile**:
   In `config/active_user.yaml`, set your profile ID:
   ```yaml
   active_profile: "wife"  # or "ayush" or "harsh"
   default_language: "en"
   ```

4. **Open in Anti-Gravity**:
   Open this folder in **Anti-Gravity**. The built-in AI Copilot will automatically read `.antigravity/rules/career-copilot.md` and act as your personalized career assistant!

---

## 🧠 How to "Train" & Customize Your Individual AI Copilot

You don't need expensive model fine-tuning; the Anti-Gravity AI is dynamically **grounded** in your profile files:

1. **Edit `profiles/<your_name>/profile.yaml`**:
   - Update your contact information, degrees, GPA, university names, key technical domains, instruments/tools, and language levels.
2. **Customize `profiles/<your_name>/bullets_en.yaml` & `bullets_de.yaml`**:
   - Add your specific accomplishments, projects, and work highlights grouped by theme (e.g. data analysis, backend engineering, hardware, project management).
3. **Talk to Anti-Gravity in Natural Language**:
   Because the workspace rules are active, you can simply tell the AI:
   - *"Anti-Gravity, I found this job posting PDF. Please analyze it against my profile and tell me my match score."*
   - *"Anti-Gravity, generate a tailored 1-page CV and Cover Letter for the Senior Consultant position at Arcadis in German."*
   - *"Anti-Gravity, draft a 300-character LinkedIn connection note to the hiring manager."*

---

## 🛠️ CLI Cheat Sheet

You can also run all pipeline commands directly from the terminal:

### 1. Ingest & Analyze Job Postings
```powershell
# Scrape a job posting from a URL and archive it
.venv\Scripts\python.exe pipeline.py scrape --url "https://www.stellenanzeigen.de/suche/..."

# Ingest a manually downloaded PDF
.venv\Scripts\python.exe pipeline.py ingest --pdf-path "job_ads_manual/New_Job.pdf"

# Analyze all jobs in the database and update job_matrix.xlsx
.venv\Scripts\python.exe pipeline.py analyze
```

### 2. Generate Tailored CV & Cover Letter PDFs
```powershell
# For Harsh (English)
.venv\Scripts\python.exe pipeline.py generate --profile harsh --company "C-Lock Inc" --role "Field Application Specialist" --lang en

# For Harsh (German)
.venv\Scripts\python.exe pipeline.py generate --profile harsh --company "ISF Schaumann" --role "Junior Product Manager" --lang de

# For Wife Profile
.venv\Scripts\python.exe pipeline.py generate --profile wife --company "Arcadis" --role "Data Analyst" --lang en

# For Ayush Profile
.venv\Scripts\python.exe pipeline.py generate --profile ayush --company "DeLaval" --role "Software Engineer" --lang en
```

### 3. CRM & Networking Outreach
```powershell
# Generate a LinkedIn connection note
.venv\Scripts\python.exe pipeline.py outreach --company "Arcadis" --contact "Dr. Schmidt" --type connection --log

# Generate a personalized cold email
.venv\Scripts\python.exe pipeline.py outreach --company "TÜV SÜD" --contact "Recruitment Team" --type email
```

### 4. Check Pipeline Status
```powershell
.venv\Scripts\python.exe pipeline.py status
```
