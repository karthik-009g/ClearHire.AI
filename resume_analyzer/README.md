# Free Resume Analyzer (No API Key)

This module adds a free resume optimizer inside the job automation repository.

## What It Does

- Upload resume files (`PDF`, `DOCX`, `TXT`)
- Extracts resume text locally
- Runs ATS-style analysis locally (no paid APIs)
- Gives score breakdown: contact, structure, impact, keyword match
- Generates optimized summary and bullet rewrite suggestions
- Supports optional job description matching
- Lets you download a text report

## Why This Is Free

- No Gemini/Claude/OpenAI API calls
- No API key required
- No billing dependency
- All logic runs in local Python code

## Folder Structure

resume-analyzer-free/
- app.py
- services/
  - ai_service.py
  - pdf_service.py
  - docx_service.py
  - resume_analyzer_service.py
- utils/
  - config.py
- requirements.txt

## Setup

### Windows

```powershell
cd resume-analyzer-free
python -m venv atsVenv
.\atsVenv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

### Mac/Linux

```bash
cd resume-analyzer-free
python3 -m venv atsVenv
source atsVenv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Then open the local Streamlit URL shown in terminal.

## Optional Enhancement

If you later want true LLM rewriting quality, you can add a paid API-backed `ai_service.py` behind a feature flag. The current default implementation is fully local and free.
