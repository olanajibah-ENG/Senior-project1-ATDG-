"""
llm_client.py — OpenRouter LLM Client
Handles rate limiting, caching, model fallback, and retries.
"""
from __future__ import annotations

import hashlib
import logging
import time
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class LLMClient:
    """
    OpenRouter API client with:
    - Response caching (48 h)
    - Rate-limit detection and block tracking
    - Automatic model fallback across free models
    - Configurable retries with exponential back-off
    """

    MAX_RETRIES  = 5
    BASE_WAIT    = 30          # seconds to wait on first rate-limit hit
    CACHE_TTL    = 3600 * 48   # 48 hours

    # ------------------------------------------------------------------
    # Cache helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _cache_key(system_prompt: str, user_prompt: str) -> str:
        digest = hashlib.md5(f"{system_prompt}|{user_prompt}".encode()).hexdigest()
        return f"llm_response_{digest}"

    @staticmethod
    def _get_cached(key: str) -> str | None:
        try:
            val = cache.get(key)
            if val:
                logger.info(f"[LLM Cache] HIT {key[:20]}…")
            return val
        except Exception as e:
            logger.warning(f"[LLM Cache] get error: {e}")
            return None

    @staticmethod
    def _set_cached(key: str, value: str) -> None:
        try:
            cache.set(key, value, LLMClient.CACHE_TTL)
            logger.info(f"[LLM Cache] SET {key[:20]}…")
        except Exception as e:
            logger.warning(f"[LLM Cache] set error: {e}")

    # ------------------------------------------------------------------
    # Rate-limit helpers
    # ------------------------------------------------------------------

    _RL_KEY = "openrouter_rate_limit_status"

    @staticmethod
    def _is_rate_limited() -> tuple[bool, float]:
        """Returns (blocked, remaining_seconds)."""
        status = cache.get(LLMClient._RL_KEY)
        if status and status.get("blocked_until"):
            until = datetime.fromisoformat(status["blocked_until"])
            if datetime.now() < until:
                return True, (until - datetime.now()).total_seconds()
        return False, 0.0

    @staticmethod
    def _set_rate_limit_block(minutes: int = 60) -> None:
        until = datetime.now() + timedelta(minutes=minutes)
        cache.set(
            LLMClient._RL_KEY,
            {"blocked_until": until.isoformat(), "blocked_at": datetime.now().isoformat()},
            minutes * 60,
        )
        logger.warning(f"[Rate Limit] Blocked until {until}")

    # ------------------------------------------------------------------
    # Main call
    # ------------------------------------------------------------------

    @staticmethod
    def call_model(
        system_prompt: str,
        user_prompt: str,
        use_cache: bool = True,
        force_request: bool = False,
        model: str | None = None,
    ) -> str:
        """
        Call OpenRouter with caching, rate-limit guard, and model fallback.

        Args:
            system_prompt:  System message text.
            user_prompt:    User message text.
            use_cache:      Return cached response when available (default True).
            force_request:  Bypass rate-limit block (default False).
            model:          Override model; None = use current default.

        Returns:
            Generated text content.

        Raises:
            Exception on unrecoverable errors.
        """
        # --- Cache check ---
        cache_key = LLMClient._cache_key(system_prompt, user_prompt) if use_cache else ""
        if use_cache:
            cached = LLMClient._get_cached(cache_key)
            if cached:
                return cached

        # --- Rate-limit guard ---
        if not force_request:
            blocked, wait = LLMClient._is_rate_limited()
            if blocked:
                raise Exception(
                    f"API temporarily blocked due to rate limit. "
                    f"Remaining: {int(wait / 60)} minutes."
                )

        # --- Setup ---
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            raise Exception("OPENROUTER_API_KEY missing in settings.")

        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "Software Documentation Agent",
            "HTTP-Referer": "http://localhost:8000",
        }

        if model is None:
            model = LLMClient.get_current_model()

        available_models = [m["model"] for m in LLMClient.get_available_free_models()]
        current_model    = model

        payload = {
            "model": current_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user",   "content": user_prompt},
            ],
            "max_tokens": 4000,
            "temperature": 0.7,
        }

        last_error: str = ""

        for attempt in range(LLMClient.MAX_RETRIES):
            try:
                logger.info(
                    f"[LLM] Attempt {attempt + 1}/{LLMClient.MAX_RETRIES} "
                    f"model={current_model}"
                )
                payload["model"] = current_model
                response = requests.post(url, headers=headers, json=payload, timeout=120)

                # --- Handle 429 / 404 with model rotation ---
                if response.status_code in (429, 404):
                    reason = "rate-limit" if response.status_code == 429 else "model-not-found"
                    logger.warning(
                        f"[LLM] {reason} on attempt {attempt + 1} "
                        f"with model {current_model}"
                    )

                    if response.status_code == 429:
                        LLMClient._set_rate_limit_block(60)
                        rl = {
                            "limit":     response.headers.get("X-RateLimit-Limit", "?"),
                            "remaining": response.headers.get("X-RateLimit-Remaining", "?"),
                            "reset":     response.headers.get("X-RateLimit-Reset", "?"),
                        }
                        last_error = (
                            f"Rate limit hit (limit={rl['limit']}, "
                            f"remaining={rl['remaining']}, reset={rl['reset']}). "
                            f"Last model: {current_model}."
                        )
                        raise Exception(last_error)

                    # 404 → rotate to next model
                    idx = available_models.index(current_model) if current_model in available_models else 0
                    current_model = available_models[(idx + 1) % len(available_models)]
                    logger.info(f"[LLM] Rotating to model: {current_model}")
                    last_error = f"Model {current_model} not available (404)."
                    time.sleep((attempt + 1) * 5)
                    continue

                # --- Other HTTP errors ---
                if response.status_code != 200:
                    ct = response.headers.get("content-type", "")
                    body = response.json() if "application/json" in ct else response.text
                    last_error = f"HTTP {response.status_code}: {body}"
                    logger.error(f"[LLM] {last_error}")
                    time.sleep((attempt + 1) * 5)
                    continue

                # --- Success ---
                result  = response.json()
                choices = result.get("choices") or []
                if not choices:
                    last_error = f"Empty choices in response: {result}"
                    logger.error(f"[LLM] {last_error}")
                    time.sleep((attempt + 1) * 5)
                    continue
                content = choices[0]["message"]["content"]

                if use_cache:
                    LLMClient._set_cached(cache_key, content)

                logger.info(f"[LLM] Success on attempt {attempt + 1}")
                return content

            except requests.exceptions.RequestException as exc:
                last_error = f"Network error: {exc}"
                logger.error(f"[LLM] {last_error}")
                time.sleep((attempt + 1) * 5)

            except Exception as exc:
                last_error = str(exc)
                logger.error(f"[LLM] Error on attempt {attempt + 1}: {exc}")
                if "rate limit" in last_error.lower() or "429" in last_error:
                    raise
                time.sleep((attempt + 1) * 5)

        raise Exception(
            f"Failed after {LLMClient.MAX_RETRIES} attempts. Last error: {last_error}"
        )

    # ------------------------------------------------------------------
    # Model management
    # ------------------------------------------------------------------

    @staticmethod
    def get_available_free_models() -> list[dict]:
        return [
            {
                "model": "openai/gpt-oss-120b:free",
                "name": "OpenAI GPT OSS 120B",
                "description": "OpenAI open model — 120B params, 131K context",
                "strengths": ["strong reasoning", "tool use", "131K context"],
                "context": "131K tokens",
            },
            {
                "model": "nvidia/nemotron-nano-9b-v2:free",
                "name": "NVIDIA Nemotron Nano 9B V2",
                "description": "Fast NVIDIA model, good for code tasks",
                "strengths": ["fast", "code-friendly", "32K context"],
                "context": "32K tokens",
            },
            {
                "model": "google/gemma-3-27b-it:free",
                "name": "Gemma 3 (27B)",
                "description": "Google large model — high accuracy",
                "strengths": ["large context", "high accuracy", "multi-task"],
                "context": "8K tokens",
            },
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "name": "Meta Llama 3.3 (70B)",
                "description": "Meta flagship free model",
                "strengths": ["very powerful", "large context", "high accuracy"],
                "context": "8K tokens",
            },
            {
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "name": "Meta Llama 3.2 (3B)",
                "description": "Lightweight Meta model — reliable",
                "strengths": ["reliable", "fast", "free"],
                "context": "4K tokens",
            },
            {
                "model": "mistralai/mistral-7b-instruct:free",
                "name": "Mistral 7B",
                "description": "Balanced Mistral model",
                "strengths": ["good performance", "fast", "reliable"],
                "context": "32K tokens",
            },
            {
                "model": "mistralai/devstral-small-2505:free",
                "name": "Mistral Devstral Small",
                "description": "Mistral model optimised for code",
                "strengths": ["code-specialised", "optimised", "free"],
                "context": "32K tokens",
            },
        ]

    @staticmethod
    def get_current_model() -> str:
        return cache.get("current_llm_model") or "openai/gpt-oss-120b:free"

    @staticmethod
    def switch_model(model_name: str) -> dict:
        valid = [m["model"] for m in LLMClient.get_available_free_models()]
        if model_name not in valid:
            raise ValueError(f"Invalid model. Available: {valid}")
        cache.set("current_llm_model", model_name, 3600)
        logger.info(f"[LLM] Switched to model: {model_name}")
        return {"status": "success", "model": model_name}

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    @staticmethod
    def get_rate_limit_info() -> dict:
        try:
            api_key = getattr(settings, "OPENROUTER_API_KEY", None)
            if not api_key:
                return {"error": "API Key missing"}
            resp = requests.get(
                "https://openrouter.ai/api/v1/auth/key",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=10,
            )
            return resp.json() if resp.status_code == 200 else {"error": resp.text}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def test_model_connection() -> dict:
        try:
            api_key = getattr(settings, "OPENROUTER_API_KEY", None)
            if not api_key:
                return {"error": "API Key missing"}
            result = LLMClient.call_model(
                "You are a helpful assistant.",
                "Respond with 'OK' only.",
                use_cache=False,
                force_request=True,
            )
            return {
                "status": "success",
                "model": LLMClient.get_current_model(),
                "response": result.strip(),
            }
        except Exception as e:
            return {
                "status": "error",
                "model": LLMClient.get_current_model(),
                "error": str(e),
            }
