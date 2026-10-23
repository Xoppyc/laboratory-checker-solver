"""Command-line interface and interactive wizard for Quiz Solver."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

from .models import AnswerDecision, Question, QuizConfig, QuizSummary
from .providers.factory import create_llm_provider
from .runner import QuizRunner

# Check if rich is available for enhanced terminal display
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table

    console = Console()
    HAS_RICH = True
except ImportError:
    console = None
    HAS_RICH = False


def print_banner() -> None:
    text = (
        "===============================================================\n"
        "       Laboratory Checker Quiz Solver (ЛНУ ФЕКТ)              \n"
        "  Autonomous DOM-based test solver with anti-detection pacing  \n"
        "==============================================================="
    )
    if HAS_RICH and console:
        console.print(Panel(text, style="bold cyan"))
    else:
        print(text)


def print_question_status(question: Question, decision: AnswerDecision, delay: float) -> None:
    line = (
        f"[{question.number:02d}/{question.total:02d}] "
        f"-> Option: [bold green]{decision.selected_label}[/bold green] "
        f"(delay {delay:.1f}s) | {question.title[:65]}..."
    )
    if HAS_RICH and console:
        console.print(line)
    else:
        # Strip simple rich tags for standard stdout
        clean_line = (
            f"[{question.number:02d}/{question.total:02d}] "
            f"-> Option: {decision.selected_label} (delay {delay:.1f}s) | {question.title[:65]}..."
        )
        print(clean_line)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Autonomous test solver for Laboratory Checker web portal."
    )
    parser.add_argument("--name", type=str, help="Student full name (e.g. 'Кириченко Артем')")
    parser.add_argument(
        "--group", type=str, help="Student academic group (e.g. 'ФеП-31', 'ФеП-32')"
    )
    parser.add_argument(
        "--course",
        type=str,
        default="professional_python",
        choices=["professional_python", "functional_programming"],
        help="Course code",
    )
    parser.add_argument(
        "--lab",
        type=str,
        default=None,
        help="Lab identifier (e.g. 'Lab_01', 'Lab_02', or 'all')",
    )
    parser.add_argument(
        "--repo",
        type=str,
        help="GitHub repository path (e.g. 'username/repository')",
    )
    parser.add_argument(
        "--provider",
        type=str,
        default="gemini",
        choices=["gemini", "groq", "openai", "ollama"],
        help="AI inference provider (default: gemini)",
    )
    parser.add_argument("--api-key", type=str, default=None, help="Provider API key")
    parser.add_argument("--model", type=str, default=None, help="Custom LLM model name")
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.2,
        help="Minimum anti-bot delay in seconds (default: 1.2)",
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=2.8,
        help="Maximum anti-bot delay in seconds (default: 2.8)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch first question, evaluate with AI, but do not submit",
    )
    parser.add_argument(
        "--interactive",
        action="store_true",
        help="Force interactive questionnaire prompt",
    )
    parser.add_argument(
        "--signature",
        "--xyc",
        dest="show_signature",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    return parser.parse_args()


def normalize_lab_name(raw_lab: str) -> str:
    """Normalize input like 'lab-03', '3', 'lab3' into 'Lab_03'."""
    cleaned = raw_lab.strip()
    if cleaned.lower() == "all":
        return "all"
    num_match = re.search(r"(\d+)", cleaned)
    if num_match:
        num = int(num_match.group(1))
        return f"Lab_{num:02d}"
    return cleaned


def interactive_prompt(args: argparse.Namespace) -> QuizConfig:
    print("\n--- Інтерактивне налаштування ---")
    name = args.name or input("Введіть Прізвище Ім'я [Кириченко Артем]: ").strip()
    if not name:
        name = "Кириченко Артем"

    group = args.group or input("Введіть групу [ФеП-31]: ").strip()
    if not group:
        group = "ФеП-31"

    course = args.course or input("Оберіть курс [professional_python]: ").strip()
    if not course:
        course = "professional_python"

    lab = args.lab or input("Оберіть лабораторну (Lab_01 .. Lab_10, або all) [Lab_01]: ").strip()
    if not lab:
        lab = "Lab_01"

    repo = args.repo or input("GitHub repository [Xoppyc/profesional-python]: ").strip()
    if not repo:
        repo = "Xoppyc/profesional-python"

    provider = args.provider or input("AI провайдер (gemini/groq/openai/ollama) [gemini]: ").strip()
    if not provider:
        provider = "gemini"

    return QuizConfig(
        student_name=name,
        group=group,
        course=course,
        lab=lab,
        repository=repo,
        provider=provider,
        api_key=args.api_key,
        model_name=args.model,
        delay_min_seconds=args.delay_min,
        delay_max_seconds=args.delay_max,
        dry_run=args.dry_run,
    )


def save_summary_log(summary: QuizSummary) -> Path:
    out_dir = Path("results")
    out_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{summary.lab}_{summary.student_name.replace(' ', '_')}.json"
    file_path = out_dir / filename

    data = {
        "student_name": summary.student_name,
        "group": summary.group,
        "course": summary.course,
        "lab": summary.lab,
        "repository": summary.repository,
        "total_questions": summary.total_questions,
        "answers_submitted": summary.answers_submitted,
        "final_score": summary.final_score,
        "history": summary.history,
    }
    file_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def execute_single_lab(config: QuizConfig) -> QuizSummary:
    msg = f"Початок тестування: {config.student_name} | {config.lab} | {config.repository}"
    if HAS_RICH and console:
        console.print(f"\n[bold yellow]{msg}[/bold yellow]")
    else:
        print(f"\n{msg}")

    provider = create_llm_provider(config)
    runner = QuizRunner(
        config=config,
        provider=provider,
        on_question_answered=print_question_status,
    )

    summary = runner.run()
    log_path = save_summary_log(summary)

    res_msg = (
        f"\n[DONE] Лабораторна {config.lab} завершена!\n"
        f"Відповідей надіслано: {summary.answers_submitted}/{summary.total_questions}\n"
        f"Результат: {summary.final_score or 'Отримано (перевірте сторінку результатів)'}\n"
        f"Детальний звіт збережено у: {log_path}"
    )

    if HAS_RICH and console:
        console.print(Panel(res_msg, style="bold green" if summary.passed else "bold red"))
    else:
        print(res_msg)

    return summary


def main() -> None:
    args = parse_arguments()
    if getattr(args, "show_signature", False):
        from . import __build_hash__, __version__

        author = bytes.fromhex(__build_hash__).decode("ascii")
        print(f"Laboratory Checker Solver v{__version__} (build: {__build_hash__})")
        print(f"Verified author: {author} (Xyc)")
        return

    print_banner()

    # Determine if we should trigger interactive mode
    if args.interactive or not (args.name and args.group and args.repo and args.lab):
        config = interactive_prompt(args)
    else:
        config = QuizConfig(
            student_name=args.name,
            group=args.group,
            course=args.course,
            lab=normalize_lab_name(args.lab),
            repository=args.repo,
            provider=args.provider,
            api_key=args.api_key,
            model_name=args.model,
            delay_min_seconds=args.delay_min,
            delay_max_seconds=args.delay_max,
            dry_run=args.dry_run,
        )

    config.lab = normalize_lab_name(config.lab)

    if config.lab.lower() == "all":
        labs = [f"Lab_{i:02d}" for i in range(1, 11)]
        for current_lab in labs:
            lab_config = QuizConfig(
                student_name=config.student_name,
                group=config.group,
                course=config.course,
                lab=current_lab,
                repository=config.repository,
                provider=config.provider,
                api_key=config.api_key,
                model_name=config.model_name,
                delay_min_seconds=config.delay_min_seconds,
                delay_max_seconds=config.delay_max_seconds,
                dry_run=config.dry_run,
            )
            execute_single_lab(lab_config)
    else:
        execute_single_lab(config)


if __name__ == "__main__":
    main()

