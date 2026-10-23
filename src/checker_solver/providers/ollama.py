"""Ollama local offline LLM provider via standard urllib."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from ..models import AnswerDecision, Question
from .base import SYSTEM_PROMPT, build_question_prompt, parse_llm_json_response


class OllamaProvider:
    """Invokes local Ollama daemon without needing external packages or API keys."""

    def __init__(self, host: str = "http://localhost:11434", model: str = "llama3.2") -> None:
        self.host = host.rstrip("/")
        self.model = model
        self.base_url = f"{self.host}/api/generate"

    def answer_question(self, question: Question) -> AnswerDecision:
        user_prompt = build_question_prompt(question)
        combined_prompt = f"{SYSTEM_PROMPT}\n\n{user_prompt}"

        payload = {
            "model": self.model,
            "prompt": combined_prompt,
            "format": "json",
            "stream": False,
        }

        req = urllib.request.Request(
            self.base_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urllib.request.urlopen(req, timeout=60.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))

        raw_text = data.get("response", "")
        valid_labels = {opt.label for opt in question.options}
        return parse_llm_json_response(raw_text, valid_labels)
