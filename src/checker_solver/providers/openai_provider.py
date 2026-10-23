"""OpenAI REST API provider via standard urllib."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ..models import AnswerDecision, Question
from .base import SYSTEM_PROMPT, build_question_prompt, parse_llm_json_response


class OpenAIProvider:
    """Invokes OpenAI Chat Completions API via standard urllib."""

    def __init__(self, api_key: str, model: str = "gpt-4o-mini") -> None:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is required to use the OpenAI provider.")
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"

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
            raise RuntimeError("OpenAI returned empty response choices.")

        raw_text = choices[0].get("message", {}).get("content", "")
        valid_labels = {opt.label for opt in question.options}
        return parse_llm_json_response(raw_text, valid_labels)
