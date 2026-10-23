"""Groq Cloud REST API provider via standard urllib."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ..models import AnswerDecision, Question
from .base import SYSTEM_PROMPT, build_question_prompt, parse_llm_json_response


class GroqProvider:
    """Invokes Groq OpenAI-compatible fast inference API via urllib."""

    def __init__(self, api_key: str, model: str = "llama-3.3-70b-versatile") -> None:
        if not api_key:
            raise ValueError("GROQ_API_KEY is required to use the Groq provider.")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"

    def answer_question(self, question: Question) -> AnswerDecision:
        user_prompt = build_question_prompt(question)
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=35.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        choices = data.get("choices", [])
        if not choices:
            raise RuntimeError("Groq returned empty response choices.")

        raw_text = choices[0].get("message", {}).get("content", "")
        valid_labels = {opt.label for opt in question.options}
        return parse_llm_json_response(raw_text, valid_labels)
