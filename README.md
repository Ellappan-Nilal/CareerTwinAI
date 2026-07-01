# CareerTwin AI – Your Personal Career Mentor

An AI-powered Streamlit app that helps students and job seekers figure out what
skills to learn, which career to pursue, how to improve their resume, and how
to prepare for interviews — all in one place.

## Features Implemented
1. **Skill Analysis** – log your current skills with proficiency levels.
2. **Career Match** – AI suggests the top 5 suitable roles based on your skills/interests.
3. **Skill Gap Analysis** – shows what's missing for a target role.
4. **Learning Roadmap** – 30/60/90-day day-by-day roadmap, with checkboxes to track progress.
5. **Project Recommendation** – beginner/intermediate/advanced project ideas per role.
6. **Resume Review** – upload a PDF resume, get an AI score + specific improvement suggestions.
7. **Mock Interview** – AI asks questions one at a time, scores your answers (0–10), gives tips.
8. **Progress Dashboard** – charts for skills breakdown, interview score history, roadmap completion.

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
streamlit run app.py
```

Then open the local URL Streamlit prints (usually `http://localhost:8501`).

## OpenAI API Key

Enter your key in the sidebar text field when the app is running (stored only
in the browser session, not saved to disk). Alternatively, set it as an
environment variable before launch:

```bash
export OPENAI_API_KEY="sk-..."
streamlit run app.py
```

## Project Structure

```
CareerTwinAI/
├── app.py              # Main Streamlit app (UI + navigation)
├── database.py         # SQLite schema + CRUD helpers
├── career_match.py     # Career role suggestions
├── skill_gap.py         # Skill gap analysis
├── roadmap.py           # Learning roadmap + project recommendations
├── interview.py         # Mock interview Q&A + scoring
├── resume_review.py     # Resume PDF review
├── dashboard.py          # Plotly charts for progress dashboard
├── prompts.py            # All AI prompt templates, centralized
├── utils.py               # OpenAI client wrapper, JSON parsing, PDF extraction
├── requirements.txt
└── assets/
```

`database.db` (SQLite) is created automatically the first time you run the app.

## Notes / Known Limitations
- All AI calls default to `gpt-4o-mini` — change the `model` parameter in
  `utils.call_ai()` if you want a different model.
- Resume review only works with text-based PDFs (not scanned image PDFs) since
  it uses PyPDF2 for extraction — OCR is not implemented.
- Mock interview questions avoid repeats only within the current session
  (tracked in `st.session_state`), not across logins.
- No authentication/password — "login" is just name + email lookup, meant for
  a single-user or trusted-demo context. Add real auth before deploying publicly.

## Future Enhancements (from original spec, not yet built)
- Voice interview
- AI avatar interviewer
- LinkedIn profile analysis
- GitHub profile analysis
- Certificate generator (FPDF is already in requirements.txt for this)
