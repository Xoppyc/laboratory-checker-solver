"""HTTP client for communicating with Laboratory Checker portal (Zero external dependencies)."""

from __future__ import annotations

import http.cookiejar
import urllib.error
import urllib.parse
import urllib.request

from .models import QuizConfig


class CheckerClientError(Exception):
    """Raised when server returns an HTTP or business logic error."""


class CheckerClient:
    """Manages session cookies and communication with the checker portal via standard urllib."""

    def __init__(self, base_url: str = "https://laboratory-checker-actions.onrender.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.cookie_jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cookie_jar)
        )
        self.default_headers = {
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64; rv:132.0) Gecko/20100101 Firefox/132.0"
            ),
            "Accept-Language": "uk-UA,uk;q=0.9,en-US;q=0.8,en;q=0.7",
        }

    def start_quiz(self, config: QuizConfig) -> str:
        """Initialize quiz session for a student and return first question HTML."""
        start_url = f"{self.base_url}/quiz/start"
        payload = {
            "student_name": config.student_name,
            "course": config.course,
            "group": config.group,
            "lab": config.lab,
            "repository": config.repository,
        }

        encoded_data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            start_url,
            data=encoded_data,
            headers=self.default_headers,
            method="POST",
        )

        try:
            with self.opener.open(req, timeout=60.0) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace").strip()
            raise CheckerClientError(
                f"Quiz start rejected by server (HTTP {err.code}):\n{err_body[:400]}"
            ) from err
        except Exception as exc:
            raise CheckerClientError(f"Failed to connect to checker server: {exc}") from exc

        if status != 200:
            raise CheckerClientError(
                f"Quiz start rejected by server (HTTP {status}):\n{body[:400]}"
            )

        if "Помилка" in body and "Питання" not in body:
            raise CheckerClientError(f"Server returned validation error:\n{body.strip()}")

        return body

    def submit_answer(self, label: str) -> tuple[str, str]:
        """Submit answer (A/B/C/D) and return (next_html, current_url)."""
        question_url = f"{self.base_url}/quiz/question"
        payload = {"answer": label}

        encoded_data = urllib.parse.urlencode(payload).encode("utf-8")
        req = urllib.request.Request(
            question_url,
            data=encoded_data,
            headers=self.default_headers,
            method="POST",
        )

        try:
            with self.opener.open(req, timeout=60.0) as resp:
                status = resp.status
                body = resp.read().decode("utf-8", errors="replace")
                current_url = resp.geturl()
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="replace").strip()
            raise CheckerClientError(
                f"Failed to submit answer (HTTP {err.code}):\n{err_body[:400]}"
            ) from err
        except Exception as exc:
            raise CheckerClientError(f"Network error while submitting answer: {exc}") from exc

        if status != 200:
            raise CheckerClientError(
                f"Failed to submit answer (HTTP {status}):\n{body[:400]}"
            )

        return body, current_url

    def close(self) -> None:
        """Cleanup session resources."""
        pass
