# Customizable CV and cover letter

This project keeps layout, reusable profile content, and job-specific data separate.

## Quick start

1. Edit `config/personal.tex` when your contact details change.
2. Edit `config/job.tex` for each application.
3. Tailor the relevant files in `content/en/` or `content/de/`.
4. Build from this directory:

```powershell
python build.py
```

The PDFs are written to `build/`:

- `cv-en.pdf`
- `cover-letter-en.pdf`
- `cv-de.pdf`
- `cover-letter-de.pdf`

To build one file only (run it twice if cross-references are added):

```powershell
xelatex -interaction=nonstopmode -output-directory=build cv-en.tex
```

## New application workflow

Copy the whole `tex-application` folder into a folder named for the employer and role. Update `config/job.tex`, tailor the profile/bullets and letter body, then compile. Keeping a separate copy per application makes the exact submitted version reproducible.

Text that usually deserves tailoring is marked with `CUSTOMIZE` comments.
