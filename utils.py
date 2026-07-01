"""
utils.py
Shared helpers: OpenAI client setup, JSON-safe parsing, PDF text extraction.
"""

import os
import json
import re
import streamlit as st
from openai import OpenAI

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


def get_api_key() -> str:
    """Priority: session state (user-entered in sidebar) > env var."""
    return st.session_state.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")


def get_client() -> OpenAI:
    api_key = get_api_key()
    if not api_key:
        raise ValueError("No OpenAI API key set. Add it in the sidebar.")
    return OpenAI(api_key=api_key)


def call_ai(system_prompt: str, user_prompt: str, model: str = "gpt-4o-mini",
            temperature: float = 0.6, json_mode: bool = False) -> str:
    """Single wrapper for all chat completion calls used across modules."""
    client = get_client()
    kwargs = {
        "model": model,
        "temperature": temperature,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message.content


def safe_json_parse(text: str, fallback=None):
    """Strip markdown code fences if present, then parse JSON safely."""
    if not text:
        return fallback
    cleaned = re.sub(r"^```json\s*|^```\s*|```$", "", text.strip(), flags=re.MULTILINE).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return fallback


def extract_pdf_text(file_obj) -> str:
    """Extract raw text from an uploaded PDF (Streamlit UploadedFile)."""
    if PdfReader is None:
        raise ImportError("PyPDF2 is not installed. Run: pip install PyPDF2")
    reader = PdfReader(file_obj)
    text_parts = []
    for page in reader.pages:
        text_parts.append(page.extract_text() or "")
    return "\n".join(text_parts).strip()
