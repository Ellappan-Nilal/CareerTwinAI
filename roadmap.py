"""
roadmap.py
Generates 30/60/90-day learning roadmaps and beginner/intermediate/advanced
project recommendations for a target role.
"""

from utils import call_ai, safe_json_parse
import prompts


def generate_roadmap(target_role: str, skills: list, duration: int = 30) -> list:
    """
    duration: 30, 60, or 90
    Returns a list of dicts: [{"day_number", "task_description"}, ...]
    """
    skills_str = ", ".join(skills) if skills else "None specified"
    user_prompt = prompts.ROADMAP_USER_TEMPLATE.format(
        target_role=target_role,
        skills=skills_str,
        duration=duration,
    )

    raw = call_ai(
        system_prompt=prompts.ROADMAP_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
        temperature=0.5,
    )

    parsed = safe_json_parse(raw, fallback={"roadmap": []})
    tasks = parsed.get("roadmap", [])
    return sorted(tasks, key=lambda t: t.get("day_number", 0))


def get_project_recommendations(target_role: str) -> dict:
    """
    Returns dict: {"beginner": [...], "intermediate": [...], "advanced": [...]}
    Each item: {"title", "description"}
    """
    user_prompt = prompts.PROJECT_RECOMMENDATION_USER_TEMPLATE.format(target_role=target_role)

    raw = call_ai(
        system_prompt=prompts.PROJECT_RECOMMENDATION_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = safe_json_parse(raw, fallback={"beginner": [], "intermediate": [], "advanced": []})
    return {
        "beginner": parsed.get("beginner", []),
        "intermediate": parsed.get("intermediate", []),
        "advanced": parsed.get("advanced", []),
    }
