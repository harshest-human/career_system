# 🚀 Neha's Anti-Gravity AI Career Copilot Guide

Welcome, **Neha**! This repository is your personal, automated **AI Career Copilot** powered by **Anti-Gravity**. 

Whenever you open this project in Anti-Gravity on your laptop, the local AI assistant is automatically **grounded and trained in your individual education, experience, and technical skillset**.

---

## ⚡ 3-Minute Quick Setup on Your Laptop

### 1. Clone & Open
```bash
git clone https://github.com/harshest-human/career_system.git
cd career_system
```
Open the `career_system` folder in **Anti-Gravity**.

### 2. Auto-Installation (Zero Effort)
- Anti-Gravity will automatically run [`setup.ps1`](file:///d:/Job%20Application/setup.ps1) in the background via [`.vscode/tasks.json`](file:///d:/Job%20Application/.vscode/tasks.json).
- It will install `uv`, create the virtual environment `.venv`, and configure the LaTeX PDF compiler.

### 3. Verify Active Profile
Open [`config/active_user.yaml`](file:///d:/Job%20Application/config/active_user.yaml) and ensure it is set to you:
```yaml
active_profile: "neha"
default_language: "en"
```

---

## 🧠 How to "Train" Your Anti-Gravity AI on Your Background

You do not need complicated machine learning fine-tuning. Anti-Gravity reads your profile directly from the `profiles/neha/` directory:

### 1. Update Your Master Details ([`profiles/neha/profile.yaml`](file:///d:/Job%20Application/profiles/neha/profile.yaml))
Edit this YAML file with your exact information:
- **Contact Details**: Phone number, email, LinkedIn URL, GitHub URL.
- **Degrees & Education**: Universities, degree titles, graduation years, and key coursework.
- **Work History**: Companies, job titles, dates, and core responsibilities.
- **Technical Skills**: Tools (Python, SQL, Power BI, Tableau, Excel, etc.) and languages (English, German, Hindi).

### 2. Add Your Key Achievements ([`profiles/neha/bullets_en.yaml`](file:///d:/Job%20Application/profiles/neha/bullets_en.yaml) & [`bullets_de.yaml`](file:///d:/Job%20Application/profiles/neha/bullets_de.yaml))
Add high-impact bullet points under your technical categories:
- **Business Intelligence & Reporting**: Dashboards, KPIs, stakeholder scorecards.
- **Data Analytics & Modeling**: Exploratory analysis, statistical validation, optimization.
- **Automation & ETL**: Python scripts, SQL procedures, automated reporting pipelines.

---

## 💬 Natural Language Prompts for Anti-Gravity Chat

You can simply chat with Anti-Gravity in natural language. Here are the best prompts to use:

### 🔍 1. Ingesting & Analyzing a Job Ad
> *"Anti-Gravity, I found this job posting PDF at `job_ads_manual/Data_Analyst_Hamburg.pdf`. Please extract the requirements, calculate my match score, and tell me where my profile stands out."*

### 📄 2. Generating a Tailored 1-Page CV & Cover Letter
> *"Anti-Gravity, generate a tailored English CV and Cover Letter for the Senior Data Analyst role at Arcadis in Hamburg. Emphasize my experience with Power BI, SQL, and process automation."*

> *(In German)*: *"Anti-Gravity, bitte erstelle meinen Lebenslauf und ein Anschreiben auf Deutsch für die Stelle als BI Spezialistin bei NordTech Solutions."*

### 🤝 3. Networking & LinkedIn Outreach
> *"Anti-Gravity, draft a polite, 300-character LinkedIn connection note to Sarah Meyer, the Head of Analytics at Arcadis, mentioning my interest in their data team."*

> *"Anti-Gravity, draft a professional cold email to the hiring manager for the Data Engineer position, highlighting my Python and ETL pipeline projects."*

---

## 🛠️ Handy Terminal Commands

If you ever want to run commands directly in the Anti-Gravity terminal:

```powershell
# Check pipeline status and see generated applications
.venv\Scripts\python.exe pipeline.py status

# Ingest and analyze all job PDFs
.venv\Scripts\python.exe pipeline.py analyze

# Scrape a job posting from a URL
.venv\Scripts\python.exe pipeline.py scrape --url "https://..." --name "Company_Role"

# Generate tailored CV and Cover Letter (English)
.venv\Scripts\python.exe pipeline.py generate --profile neha --company "Arcadis" --role "Senior Data Analyst" --lang en

# Generate tailored CV and Cover Letter (German)
.venv\Scripts\python.exe pipeline.py generate --profile neha --company "NordTech" --role "Datenanalystin" --lang de

# Generate LinkedIn outreach note
.venv\Scripts\python.exe pipeline.py outreach --profile neha --company "Arcadis" --contact "Sarah Meyer" --type connection --log
```

---

## 📂 Where Your Final PDFs Are Saved

Every time you generate an application, your compiled PDFs will be neatly organized inside:
```
outputs/neha/<Company>_<Role>_<lang>/
├── CV_Neha_Sahu_<lang>.pdf
└── CoverLetter_Neha_Sahu_<lang>.pdf
```
These PDFs are ready for instant review and direct submission to recruiters!
