"""
career_match.py
Suggests suitable career roles based on the user's current skills and interests.
"""

from utils import call_ai, safe_json_parse
import prompts


def get_career_matches(skills: list, interests: str = "") -> list:
    """
    Returns a list of dicts: [{"role_name", "match_score", "rationale"}, ...]
    """
    skills_str = ", ".join(skills) if skills else "None specified"
    user_prompt = prompts.CAREER_MATCH_USER_TEMPLATE.format(
        skills=skills_str,
        interests=interests or "None specified",
    )

    raw = call_ai(
        system_prompt=prompts.CAREER_MATCH_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = safe_json_parse(raw, fallback={"matches": []})
    return parsed.get("matches", [])
