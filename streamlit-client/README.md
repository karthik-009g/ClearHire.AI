# Streamlit Client for Job Assistant Backend

This app is a lightweight UI client for your FastAPI backend.

## Features

- Multipage Streamlit UI
- Upload resume (`/api/resumes/upload`)
- Match JD (`/api/resumes/match`)
- Tailor resume with copy-safe versioning (`/api/resumes/tailor`)
- Resume versions listing (`/api/resumes/{id}/versions`)
- View and update applications (`/api/applications/`)
- Required auth flow (`/api/auth/*`)
- Scheduler settings and source preferences (`/api/jobs/preferences`)
- Embedding-ranked scrape and top-match digest trigger (`/api/jobs/scrape`)
- Autofill is currently on hold

## Run

```powershell
cd streamlit-client
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Set backend URL in the sidebar (default: `http://127.0.0.1:8000`).

## Pages

- Home
- Upload Resume
- Match JD
- Tailor Resume
- Applications
- Auth
- Job Preferences
- Job Scrape and Digest
