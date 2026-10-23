"""Factory for instantiating LLM providers based on user preferences and environment."""

from __future__ import annotations

import os

from ..models import QuizConfig
from .base import LLMProvider
from .gemini import GeminiProvider
from .groq import GroqProvider
from .ollama import OllamaProvider
from .openai_provider import OpenAIProvider


def create_llm_provider(config: QuizConfig) -> LLMProvider:
    """Instantiate the appropriate LLM provider based on config and env vars."""
    provider_name = config.provider.lower().strip()

    if provider_name == "gemini":
        api_key = config.api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "Gemini API key is required. Set GEMINI_API_KEY environment variable or pass --api-key.\n"
                "Get a free key instantly at https://aistudio.google.com/app/apikey"
            )
        model = config.model_name or "gemini-flash-lite-latest"
        return GeminiProvider(api_key=api_key, model=model)

    if provider_name == "groq":
        api_key = config.api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError(
                "Groq API key is required. Set GROQ_API_KEY environment variable or pass --api-key.\n"
                "Get a free key instantly at https://console.groq.com/keys"
            )
        model = config.model_name or "llama-3.3-70b-versatile"
        return GroqProvider(api_key=api_key, model=model)

    if provider_name in {"openai", "chatgpt"}:
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable or pass --api-key."
            )
        model = config.model_name or "gpt-4o-mini"
        return OpenAIProvider(api_key=api_key, model=model)

    if provider_name == "ollama":
        host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        model = config.model_name or "llama3.2"
        return OllamaProvider(host=host, model=model)

    raise ValueError(
        f"Unsupported provider '{config.provider}'. Supported providers: gemini, groq, openai, ollama."
    )

