"""Google Gemini REST API provider using standard Python library (zero dependencies)."""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request

from ..models import AnswerDecision, Question
from .base import SYSTEM_PROMPT, build_question_prompt, parse_llm_json_response


class GeminiProvider:
    """Invokes Google Gemini generative language REST API via urllib."""

    def __init__(self, api_key: str, model: str = "gemini-flash-lite-latest") -> None:
        if not api_key:
            raise ValueError("GEMINI_API_KEY is required to use the Gemini provider.")
        self.api_key = api_key
        clean_model = model.replace("models/", "")
        self.model = clean_model

    def answer_question(self, question: Question) -> AnswerDecision:
        user_prompt = build_question_prompt(question)
        payload = {
            "system_instruction": {
                "parts": [{"text": SYSTEM_PROMPT}]
            },
            "contents": [
                {
                    "parts": [{"text": user_prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }

        encoded_json = json.dumps(payload).encode("utf-8")
        models_to_try = [self.model, "gemini-flash-lite-latest", "gemini-3.8-flash"]
        unique_models = list(dict.fromkeys(models_to_try))

        last_error = None
        for attempt in range(4):
            for current_model in unique_models:
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"{current_model}:generateContent?key={self.api_key}"
                )
                req = urllib.request.Request(
                    url,
                    data=encoded_json,
                    headers={"Content-Type": "application/json"},
                    method="POST",
                )

                try:
                    with urllib.request.urlopen(req, timeout=35.0) as resp:
                        body = resp.read().decode("utf-8")
                        data = json.loads(body)

                    candidates = data.get("candidates", [])
                    if not candidates:
                        continue

                    parts = candidates[0].get("content", {}).get("parts", [])
                    raw_text = parts[0].get("text", "") if parts else ""
                    valid_labels = {opt.label for opt in question.options}
                    return parse_llm_json_response(raw_text, valid_labels)

                except urllib.error.HTTPError as http_err:
                    last_error = http_err
                    if http_err.code in {429, 503, 404}:
                        time.sleep(2.0)
                        continue
                    time.sleep(1.5)
                    continue
                except Exception as exc:
                    last_error = exc
                    time.sleep(2.0)
                    continue

        raise RuntimeError(f"All Gemini models failed after retries: {last_error}")
