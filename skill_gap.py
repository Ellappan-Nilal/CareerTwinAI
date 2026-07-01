"""
skill_gap.py
Analyzes the gap between a user's current skills and a target role's requirements.
"""

from utils import call_ai, safe_json_parse
import prompts


def get_skill_gaps(skills: list, target_role: str) -> list:
    """
    Returns a list of dicts: [{"skill", "priority", "reason"}, ...]
    """
    skills_str = ", ".join(skills) if skills else "None specified"
    user_prompt = prompts.SKILL_GAP_USER_TEMPLATE.format(
        skills=skills_str,
        target_role=target_role,
    )

    raw = call_ai(
        system_prompt=prompts.SKILL_GAP_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
    )

    parsed = safe_json_parse(raw, fallback={"gaps": []})
    return parsed.get("gaps", [])
