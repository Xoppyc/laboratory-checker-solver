"""Orchestrates quiz execution from start to final results page."""

from __future__ import annotations

import random
import time
from typing import Callable

from .client import CheckerClient
from .models import AnswerDecision, Question, QuizConfig, QuizSummary
from .parser import extract_results_info, is_result_page, parse_quiz_page
from .providers.base import LLMProvider

QuestionCallback = Callable[[Question, AnswerDecision, float], None]


class QuizRunner:
    """Automates solving 50 test questions with anti-detection delays."""

    def __init__(
        self,
        config: QuizConfig,
        provider: LLMProvider,
        on_question_answered: QuestionCallback | None = None,
    ) -> None:
        self.config = config
        self.provider = provider
        self.client = CheckerClient(base_url=config.base_url)
        self.on_question_answered = on_question_answered

    def run(self) -> QuizSummary:
        summary = QuizSummary(
            student_name=self.config.student_name,
            course=self.config.course,
            group=self.config.group,
            lab=self.config.lab,
            repository=self.config.repository,
            total_questions=50,
            answers_submitted=0,
        )

        try:
            current_html = self.client.start_quiz(self.config)

            for step in range(1, 65):
                # Check if we have already reached the result page
                if is_result_page(current_html):
                    res_info = extract_results_info(current_html)
                    summary.final_score = res_info.get("score_text")
                    summary.passed = True
                    return summary

                question = parse_quiz_page(current_html)
                summary.total_questions = question.total

                # Query AI model for the answer
                decision = self.provider.answer_question(question)

                if self.config.dry_run:
                    if self.on_question_answered:
                        self.on_question_answered(question, decision, 0.0)
                    summary.answers_submitted += 1
                    summary.history.append({
                        "number": question.number,
                        "title": question.title,
                        "selected": decision.selected_label,
                        "reasoning": decision.reasoning,
                    })
                    break

                # Apply randomized human-like delay to prevent aggressive bot flagging
                delay = random.uniform(
                    self.config.delay_min_seconds,
                    self.config.delay_max_seconds,
                )
                time.sleep(delay)

                # Submit answer to server
                next_html, current_url = self.client.submit_answer(decision.selected_label)
                summary.answers_submitted += 1
                summary.history.append({
                    "number": question.number,
                    "title": question.title,
                    "selected": decision.selected_label,
                    "reasoning": decision.reasoning,
                    "delay_seconds": round(delay, 2),
                })

                if self.on_question_answered:
                    self.on_question_answered(question, decision, delay)

                # Check if the subsequent page is the result
                if is_result_page(next_html) or "/quiz/result" in current_url:
                    res_info = extract_results_info(next_html)
                    summary.final_score = res_info.get("score_text")
                    summary.passed = True
                    return summary

                current_html = next_html

            return summary

        finally:
            self.client.close()

