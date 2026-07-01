"""
interview.py
AI mock interview: generates questions one at a time, evaluates answers,
scores them, and gives improvement tips.
"""

from utils import call_ai, safe_json_parse
import prompts


def get_next_question(target_role: str, difficulty: str = "Medium", previous_questions: list = None) -> str:
    previous_questions = previous_questions or []
    prev_str = "; ".join(previous_questions) if previous_questions else "None yet"

    user_prompt = prompts.INTERVIEW_QUESTION_USER_TEMPLATE.format(
        target_role=target_role,
        difficulty=difficulty,
        previous_questions=prev_str,
    )

    raw = call_ai(
        system_prompt=prompts.INTERVIEW_QUESTION_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
        temperature=0.8,
    )

    parsed = safe_json_parse(raw, fallback={"question": "Tell me about yourself."})
    return parsed.get("question", "Tell me about yourself.")


def evaluate_answer(question: str, answer: str, target_role: str) -> dict:
    """
    Returns dict: {"score" (0-10), "feedback", "improvement_tips"}
    """
    if not answer or not answer.strip():
        return {
            "score": 0,
            "feedback": "No answer provided.",
            "improvement_tips": ["Try to attempt every question, even a partial answer scores better than none."],
        }

    user_prompt = prompts.INTERVIEW_EVALUATION_USER_TEMPLATE.format(
        question=question,
        answer=answer,
        target_role=target_role,
    )

    raw = call_ai(
        system_prompt=prompts.INTERVIEW_EVALUATION_SYSTEM,
        user_prompt=user_prompt,
        json_mode=True,
        temperature=0.3,
    )

    parsed = safe_json_parse(raw, fallback={"score": 0, "feedback": "Could not evaluate.", "improvement_tips": []})
    return parsed
