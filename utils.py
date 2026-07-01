"""
utils.py
Shared helpers: Gemini API client setup, JSON-safe parsing, PDF text extraction.
"""

import os
import json
import re
import streamlit as st
import google.generativeai as genai

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None


def get_api_key() -> str:
    """Priority: session state (user-entered in sidebar) > env var."""
    return st.session_state.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY", "")


def call_ai(system_prompt: str, user_prompt: str, model: str = "gemini-pro",
            temperature: float = 0.6, json_mode: bool = False) -> str:
    """Single wrapper for all chat completion calls used across modules."""
    api_key = get_api_key()
    if not api_key:
        raise ValueError("No Gemini API key set. Add it in the sidebar.")
    
    genai.configure(api_key=api_key)
    
    generation_config = {
        "temperature": temperature,
    }
        
    client = genai.GenerativeModel(
        model_name=model,
        generation_config=generation_config
    )
    
    # Gemini 1.0 (gemini-pro) does not natively support system_instruction
    # so we combine the system prompt and user prompt manually.
    combined_prompt = f"System Instructions:\n{system_prompt}\n\nUser Request:\n{user_prompt}"
    
    response = client.generate_content(combined_prompt)
    return response.text


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
