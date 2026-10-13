"""Multi-provider LLM integration for grounded answer generation.

Supports:
- "local": FLAN-T5 via HuggingFace transformers (default, no API key needed)
- "openai": OpenAI API (GPT-4o-mini, GPT-4o, etc.)
- "gemini": Google Gemini API
- "ollama": Local Ollama models (Phi-3, Llama 3.2, etc.)

Set LLM_PROVIDER and LLM_MODEL_NAME in .env to choose.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Any, Callable, Optional

from src.config import settings

logger = logging.getLogger(__name__)

DEFAULT_MAX_NEW_TOKENS = 256
DEFAULT_LLM_MODEL = "google/flan-t5-base"

_PROMPT_TEMPLATE = """You are a careful medical-reference assistant. Answer the question using ONLY the context below, which is taken from a medical encyclopedia. If the context does not contain enough information to answer, say so plainly and recommend the user consult a healthcare professional. Do not add facts that are not in the context.

Context:
{context}

Question: {question}

Answer:"""


class LLMLoadError(RuntimeError):
    """Raised when the LLM fails to load or configure."""


class GenerationError(RuntimeError):
    """Raised when text generation fails."""


@lru_cache(maxsize=2)
def load_model(model_name: Optional[str] = None) -> Any:
    """Initialize and return an LLM client/pipeline based on LLM_PROVIDER.

    Args:
        model_name: Optional override for the model name. If not provided,
            uses settings.llm_model_name, or a provider-specific default.

    Returns:
        An object (pipeline, client, or config dict) that `generate_answer()`
        knows how to use.

    Raises:
        LLMLoadError: If the provider is invalid or fails to initialize.
    """
    provider = settings.llm_provider.lower()
    
    if provider == "local":
        model_to_use = model_name or settings.llm_model_name or "google/flan-t5-base"
        logger.info("Loading local HuggingFace model: %s", model_to_use)
        try:
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer, pipeline
            tokenizer = AutoTokenizer.from_pretrained(model_to_use)
            model = AutoModelForSeq2SeqLM.from_pretrained(model_to_use)
            return pipeline("text2text-generation", model=model, tokenizer=tokenizer)
        except Exception as exc:
            raise LLMLoadError(f"Failed to load local LLM '{model_to_use}': {exc}") from exc

    elif provider == "openai":
        model_to_use = model_name or (settings.llm_model_name if settings.llm_model_name != "google/flan-t5-base" else "gpt-4o-mini")
        logger.info("Configuring OpenAI API with model: %s", model_to_use)
        if not settings.openai_api_key:
            raise LLMLoadError("OPENAI_API_KEY is not set.")
        try:
            import openai
            client = openai.OpenAI(api_key=settings.openai_api_key)
            return {"provider": "openai", "client": client, "model": model_to_use}
        except ImportError as exc:
            raise LLMLoadError("openai package not installed. Run: pip install openai") from exc

    elif provider == "gemini":
        model_to_use = model_name or (settings.llm_model_name if settings.llm_model_name != "google/flan-t5-base" else "gemini-2.0-flash")
        logger.info("Configuring Gemini API with model: %s", model_to_use)
        if not settings.gemini_api_key:
            raise LLMLoadError("GEMINI_API_KEY is not set.")
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.gemini_api_key)
            return {"provider": "gemini", "model": model_to_use}
        except ImportError as exc:
            raise LLMLoadError("google-generativeai package not installed. Run: pip install google-generativeai") from exc

    elif provider == "ollama":
        model_to_use = model_name or (settings.llm_model_name if settings.llm_model_name != "google/flan-t5-base" else "phi3")
        logger.info("Configuring Ollama API with model: %s", model_to_use)
        try:
            import requests
            return {"provider": "ollama", "base_url": settings.ollama_base_url, "model": model_to_use}
        except ImportError as exc:
            raise LLMLoadError("requests package not installed.") from exc

    else:
        raise LLMLoadError(f"Unknown LLM_PROVIDER: {provider}")


def build_prompt(context: str, question: str, max_context_chars: Optional[int] = None) -> str:
    """Assemble the grounded RAG prompt."""
    max_chars = max_context_chars or settings.max_context_chars
    context = (context or "").strip()
    if len(context) > max_chars:
        context = context[:max_chars].rsplit(" ", 1)[0] + "…"
    context = context or "(no relevant context was found)"
    return _PROMPT_TEMPLATE.format(context=context, question=question.strip())


def generate_answer(
    context: str,
    question: str,
    text_generator: Optional[Any] = None,
    max_new_tokens: int = DEFAULT_MAX_NEW_TOKENS,
) -> str:
    """Generate an answer to `question`, grounded in retrieved `context`.

    Args:
        context: Retrieved chunk text.
        question: The user's raw question.
        text_generator: Client/pipeline returned by `load_model()`.
        max_new_tokens: Generation length cap.

    Returns:
        The generated answer.
    """
    if text_generator is None:
        text_generator = load_model()

    provider = settings.llm_provider.lower()
    
    # Auto-adjust context chars if using an API provider and not explicitly set
    max_chars = settings.max_context_chars
    if provider in ("openai", "gemini") and max_chars == 1800:
        max_chars = 100000

    prompt = build_prompt(context, question, max_context_chars=max_chars)
    logger.debug("Prompt sent to LLM (%d chars): %s", len(prompt), prompt)

    if provider == "local":
        return _generate_local(prompt, text_generator, max_new_tokens)
    elif provider == "openai":
        return _generate_openai(prompt, text_generator, max_new_tokens)
    elif provider == "gemini":
        return _generate_gemini(prompt, text_generator, max_new_tokens)
    elif provider == "ollama":
        return _generate_ollama(prompt, text_generator, max_new_tokens)
    else:
        raise GenerationError(f"Unknown provider: {provider}")


def _generate_local(prompt: str, pipeline_obj: Any, max_new_tokens: int) -> str:
    try:
        outputs = pipeline_obj(
            prompt,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            num_beams=4,
            repetition_penalty=1.3,
            truncation=True,
        )
    except Exception as exc:
        raise GenerationError(f"FLAN-T5 generation failed: {exc}") from exc

    if not outputs:
        raise GenerationError("FLAN-T5 returned no output.")
    
    answer = outputs[0]["generated_text"].strip()
    return answer or "I don't have enough information in the provided context to answer that."


def _generate_openai(prompt: str, config: dict, max_new_tokens: int) -> str:
    try:
        client = config["client"]
        response = client.chat.completions.create(
            model=config["model"],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_new_tokens,
            temperature=0.0,
        )
        answer = response.choices[0].message.content.strip()
        return answer or "I don't have enough information in the provided context to answer that."
    except Exception as exc:
        raise GenerationError(f"OpenAI generation failed: {exc}") from exc


def _generate_gemini(prompt: str, config: dict, max_new_tokens: int) -> str:
    try:
        import google.generativeai as genai
        model = genai.GenerativeModel(config["model"])
        response = model.generate_content(
            prompt,
            generation_config=genai.types.GenerationConfig(
                temperature=0.0,
                max_output_tokens=max_new_tokens,
            )
        )
        answer = response.text.strip()
        return answer or "I don't have enough information in the provided context to answer that."
    except Exception as exc:
        raise GenerationError(f"Gemini generation failed: {exc}") from exc


def _generate_ollama(prompt: str, config: dict, max_new_tokens: int) -> str:
    try:
        import requests
        url = f"{config['base_url'].rstrip('/')}/api/generate"
        payload = {
            "model": config["model"],
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
                "num_predict": max_new_tokens
            }
        }
        response = requests.post(url, json=payload, timeout=60)
        response.raise_for_status()
        answer = response.json().get("response", "").strip()
        return answer or "I don't have enough information in the provided context to answer that."
    except Exception as exc:
        raise GenerationError(f"Ollama generation failed: {exc}") from exc
