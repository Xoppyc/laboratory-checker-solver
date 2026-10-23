"""HTML parser for Laboratory Checker quiz pages."""

from __future__ import annotations

import html
import re
from typing import Any

from .models import Question, QuestionOption


class QuizParserError(Exception):
    """Raised when an HTML quiz page cannot be parsed."""


def clean_html_text(raw_text: str) -> str:
    """Strip HTML tags, decode entities, and normalize whitespace."""
    # Convert <br> and paragraph endings to newlines before tag stripping
    text = re.sub(r"<(?:br|/p|/div|/h\d)>", "\n", raw_text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    # Normalize multiple whitespaces while preserving intentional lines
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line).strip()


def parse_quiz_page(html_content: str) -> Question:
    """Extract question number, total questions, question prompt, and options."""
    # Extract progress counter (e.g. "Питання 4 із 50")
    progress_match = re.search(r"Питання\s+(\d+)\s+із\s+(\d+)", html_content)
    if progress_match:
        number = int(progress_match.group(1))
        total = int(progress_match.group(2))
    else:
        number = 1
        total = 50

    # Extract question title/body from <h2>...</h2>
    h2_match = re.search(r"<h2>(.*?)</h2>", html_content, flags=re.DOTALL)
    if not h2_match:
        raise QuizParserError("Could not find question header (<h2>) in response HTML.")

    raw_title = h2_match.group(1)
    title = clean_html_text(raw_title)

    # Extract options: <input value="X"> followed by <strong>X.</strong> option text
    options: list[QuestionOption] = []
    # Pattern matching the standard checker radio container
    label_pattern = re.compile(
        r'<label[^>]*class=[\'"]answer[\'"][^>]*>.*?'
        r'<input[^>]*value=[\'"]([A-D])[\'"][^>]*>.*?'
        r'<strong>\s*([A-D])\.\s*</strong>(.*?)'
        r'</label>',
        flags=re.DOTALL,
    )

    for match in label_pattern.finditer(html_content):
        val = match.group(1)
        raw_opt_text = match.group(3)
        opt_text = clean_html_text(raw_opt_text)
        options.append(QuestionOption(label=val, text=opt_text))

    if not options:
        # Fallback broader pattern if class names or markup shift slightly
        fallback_pattern = re.compile(
            r'<input[^>]*name=[\'"]answer[\'"][^>]*value=[\'"]([A-D])[\'"][^>]*>.*?'
            r'<strong>\s*([A-D])\.\s*</strong>(.*?)(?:</label>|<input|<button)',
            flags=re.DOTALL,
        )
        for match in fallback_pattern.finditer(html_content):
            val = match.group(1)
            opt_text = clean_html_text(match.group(3))
            options.append(QuestionOption(label=val, text=opt_text))

    if not options:
        raise QuizParserError("No answer options (A, B, C, D) found in the question form.")

    return Question(number=number, total=total, title=title, options=options)


def is_result_page(html_content: str) -> bool:
    """Check if the response represents the final test completion / results page."""
    markers = [
        "Результати тестування",
        "Тестування завершено",
        "Ваш результат",
        "Оцінка",
        "Бал:",
        "Правильних відповідей",
    ]
    return any(marker in html_content for marker in markers)


def extract_results_info(html_content: str) -> dict[str, Any]:
    """Extract score, percentage, and summary text from the results page."""
    clean_text = clean_html_text(html_content)
    score_match = re.search(r"(\d+)\s*(?:із|/)\s*(\d+)", clean_text)
    percent_match = re.search(r"(\d+(?:\.\d+)?)\s*%", clean_text)

    score_str = score_match.group(0) if score_match else None
    percent_str = percent_match.group(1) if percent_match else None

    return {
        "score_text": score_str,
        "percentage": percent_str,
        "raw_summary": clean_text[:600],
    }

