"""Abstract base protocol and prompt templates for LLM providers."""

from __future__ import annotations

import json
import re
from typing import Protocol

from ..models import AnswerDecision, Question


class LLMProvider(Protocol):
    """Protocol for pluggable AI decision engines."""

    def answer_question(self, question: Question) -> AnswerDecision:
        """Analyze the question and candidate options, then return chosen label and reasoning."""
        ...


SYSTEM_PROMPT = """Ти — провідний експерт з мови Python та викладач комп'ютерних наук.
Твоє завдання — відповісти на тестове питання з університетського курсу з максимальною точністю (100% правильних відповідей).

ПРАВИЛА:
1. Уважно прочитай питання та всі варіанти відповідей.
2. Звертай особливу увагу на тонкощі Python (PEP 8, @dataclass, typing, src-layout, pytest, decorators, generators, asyncio, Docker, CI/CD).
3. Обери рівно одну правильну букву з наданих варіантів (A, B, C або D).
4. Твоя відповідь ОБОВ'ЯЗКОВО повинна бути валідним JSON-об'єктом наступного формату:
{
  "answer": "A",
  "reasoning": "Коротке пояснення, чому цей варіант єдино правильний."
}
5. Не додавай зайвого тексту поза межами JSON.
"""


def build_question_prompt(question: Question) -> str:
    """Format a question and its options into an LLM user prompt."""
    options_text = "\n".join(f"{opt.label}. {opt.text}" for opt in question.options)
    return (
        f"Питання {question.number} із {question.total}:\n"
        f"{question.title}\n\n"
        f"Варіанти відповідей:\n"
        f"{options_text}\n\n"
        "Обери правильну відповідь та поверни JSON з ключами 'answer' та 'reasoning'."
    )


def parse_llm_json_response(raw_text: str, valid_labels: set[str]) -> AnswerDecision:
    """Parse JSON or extract label fallback from raw LLM output text."""
    # Attempt 1: direct or markdown-stripped JSON decode
    cleaned = raw_text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

    try:
        data = json.loads(cleaned)
        if isinstance(data, dict) and "answer" in data:
            ans = str(data["answer"]).strip().upper()
            if ans in valid_labels:
                return AnswerDecision(
                    selected_label=ans,
                    reasoning=str(data.get("reasoning", "")).strip(),
                )
    except Exception:
        pass

    # Attempt 2: regex extract JSON object
    json_match = re.search(r"\{[^{}]*\"answer\"\s*:\s*\"([A-D])\"[^{}]*\}", raw_text)
    if json_match:
        try:
            data = json.loads(json_match.group(0))
            ans = str(data["answer"]).strip().upper()
            if ans in valid_labels:
                return AnswerDecision(
                    selected_label=ans,
                    reasoning=str(data.get("reasoning", "")).strip(),
                )
        except Exception:
            pass

    # Attempt 3: look for explicit single letter answer indicator
    label_match = re.search(r"(?:відповідь|answer)[:\s*]+([A-D])\b", raw_text, re.IGNORECASE)
    if label_match:
        ans = label_match.group(1).upper()
        if ans in valid_labels:
            return AnswerDecision(
                selected_label=ans,
                reasoning="Extracted from textual reply.",
            )

    # Attempt 4: first valid letter found
    for char in raw_text:
        char_upper = char.upper()
        if char_upper in valid_labels:
            return AnswerDecision(
                selected_label=char_upper,
                reasoning="Fallback first detected valid option.",
            )

    # Ultimate fallback: return first option
    first_opt = sorted(valid_labels)[0] if valid_labels else "A"
    return AnswerDecision(
        selected_label=first_opt,
        reasoning="Default fallback option.",
    )

