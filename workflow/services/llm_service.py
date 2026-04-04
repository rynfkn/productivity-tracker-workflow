import json
import os
import re
from pathlib import Path
from datetime import datetime
from typing import Any
from langchain_google_genai import ChatGoogleGenerativeAI

PROMPT_DIR = Path(__file__).resolve().parent.parent / "prompts"
ISO_DATETIME_RE = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?(?:Z|[+-]\d{2}:?\d{2})?)")
ISO_DATE_RE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _extract_deadline_fallback(text: str) -> str | None:
    match_dt = ISO_DATETIME_RE.search(text)
    if match_dt:
        raw = match_dt.group(1).replace(" ", "T")
        if raw.endswith("Z"):
            raw = raw[:-1] + "+00:00"
        try:
            return datetime.fromisoformat(raw).isoformat()
        except ValueError:
            return None

    match_date = ISO_DATE_RE.search(text)
    if match_date:
        # Default date-only to 09:00 local-naive; backend can normalize timezone policy.
        return f"{match_date.group(1)}T09:00:00"

    return None


def _load_prompt(name: str) -> str:
    path = PROMPT_DIR / f"{name}.md"
    if path.exists():
        return path.read_text().strip()
    return ""


def _fallback_intent(text: str) -> dict[str, Any]:
    t = (text or "").lower()
    if any(k in t for k in ["done", "finished", "completed", "yes"]):
        return {
            "intent": "done",
            "confidence": 0.8,
            "reason": "keyword_match",
            "new_deadline": None,
        }
    if any(k in t for k in ["later", "postpone", "tomorrow", "reschedule", "delay"]):
        return {
            "intent": "reschedule",
            "confidence": 0.75,
            "reason": "keyword_match",
            "new_deadline": _extract_deadline_fallback(text),
        }
    return {
        "intent": "failed",
        "confidence": 0.6,
        "reason": "default_fallback",
        "new_deadline": None,
    }


def classify_intent(user_text: str) -> dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return _fallback_intent(user_text)

    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0
        )

        prompt_template = _load_prompt("intent_classification")
        if prompt_template:
            prompt = prompt_template.replace("{user_text}", user_text)
        else:
            prompt = (
                "Classify the user's response regarding their activity.\n"
                "Intent options: done | reschedule | failed.\n"
                "If reschedule, include new_deadline as ISO datetime string or null.\n"
                "Reply with valid JSON only: "
                '{"intent":"done|reschedule|failed","confidence":0.0,"reason":"...","new_deadline":null}\n'
                f'User response: "{user_text}"'
            )

        resp = llm.invoke(prompt)
        
        # Depending on LangChain version, response could be string or AIMessage
        content = resp.content if hasattr(resp, "content") else str(resp)
        raw = content.strip()
        
        # Clean up any potential markdown formatting (e.g., ```json ... ```)
        if raw.startswith("```"):
            lines = raw.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            raw = "\n".join(lines).strip()

        data = json.loads(raw)
        if data.get("intent") not in {"done", "reschedule", "failed"}:
            return _fallback_intent(user_text)
        if "new_deadline" not in data:
            data["new_deadline"] = None
        if data.get("intent") == "reschedule" and not data.get("new_deadline"):
            data["new_deadline"] = _extract_deadline_fallback(user_text)
        return data
    except Exception as e:
        print(f"Gemini LangChain Error: {e}")
        return _fallback_intent(user_text)