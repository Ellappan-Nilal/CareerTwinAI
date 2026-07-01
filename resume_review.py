"""
resume_review.py
Extracts text from an uploaded resume PDF and generates AI-powered improvement suggestions.
Supports optional portfolio projects for richer, project-aware feedback.
"""

from utils import call_ai, safe_json_parse, extract_pdf_text
import prompts


def _format_projects(projects: list) -> str:
    """Format a list of project dicts into a readable string for the AI prompt."""
    if not projects:
        return "None provided."
    lines = []
    for p in projects:
        line = f"- **{p['title']}**: {p.get('description', '')} | Tech: {p.get('tech_stack', 'N/A')}"
        if p.get("link"):
            line += f" | Link: {p['link']}"
        lines.append(line)
    return "\n".join(lines)


def review_resume(pdf_file, target_role: str = "", projects: list = None) -> dict:
    """
    pdf_file  : Streamlit UploadedFile (PDF)
    projects  : list of project dicts {title, description, tech_stack, link}
    Returns dict: {overall_score, strengths, improvements, missing_sections, project_feedback}
    """
    resume_text = extract_pdf_text(pdf_file)
    if not resume_text:
        return {
            "overall_score": 0,
            "strengths": [],
            "improvements": [{"area": "Extraction", "suggestion": "Could not extract text. Try a text-based PDF, not a scanned image."}],
            "missing_sections": [],
            "project_feedback": [],
        }

    # Guard against extremely long resumes blowing up the prompt
    resume_text = resume_text[:8000]

    projects_text = _format_projects(projects or [])

    user_prompt = prompts.RESUME_REVIEW_USER_TEMPLATE.format(
        resume_text=resume_text,
        target_role=target_role or "Not specified",
        projects_text=projects_text,
    )

    raw = call_ai(
        system_prompt=prompts.RESUME_REVIEW_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = safe_json_parse(raw, fallback={
        "overall_score": 0,
        "strengths": [],
        "improvements": [],
        "missing_sections": [],
        "project_feedback": [],
    })
    return parsed
