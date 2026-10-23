"""Domain models and schemas for Laboratory Checker Quiz Solver."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class QuestionOption:
    """Represents a single answer choice in a multiple-choice question."""

    label: str  # 'A', 'B', 'C', 'D'
    text: str


@dataclass(slots=True)
class Question:
    """Represents an active quiz question extracted from the DOM."""

    number: int
    total: int
    title: str
    options: list[QuestionOption]


@dataclass(slots=True)
class AnswerDecision:
    """LLM decision for a question with rationale."""

    selected_label: str  # 'A', 'B', 'C', 'D'
    reasoning: str


@dataclass(slots=True)
class QuizConfig:
    """Runtime configuration for the quiz execution session."""

    student_name: str
    group: str
    course: str = "professional_python"
    lab: str = "Lab_01"
    repository: str = "Xoppyc/profesional-python"
    base_url: str = "https://laboratory-checker-actions.onrender.com"
    provider: str = "gemini"  # gemini, groq, openai, ollama
    api_key: str | None = None
    model_name: str | None = None
    delay_min_seconds: float = 1.2
    delay_max_seconds: float = 2.8
    dry_run: bool = False


@dataclass(slots=True)
class QuizSummary:
    """Final summary of a completed or aborted quiz run."""

    student_name: str
    course: str
    group: str
    lab: str
    repository: str
    total_questions: int
    answers_submitted: int
    final_score: str | None = None
    passed: bool = False
    history: list[dict[str, Any]] = field(default_factory=list)

