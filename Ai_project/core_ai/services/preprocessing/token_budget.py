import logging
logger = logging.getLogger(__name__)

MODEL_LIMITS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-3.5-turbo": 16000,
    "llama-3.3": 8000,
    "gemma-3": 8000,
    "default": 8000,
}

def estimate_tokens(text: str) -> int:
    """تقريب آمن: 1 token ≈ 3.5 حرف للنصوص المختلطة"""
    return max(1, int(len(text) / 3.5))

def get_safe_budget(model_name: str = "default") -> int:
    limit = MODEL_LIMITS.get(model_name.lower(), MODEL_LIMITS["default"])
    # نترك 1500 للخرج + 1000 للبرومت الثابت
    return max(1000, limit - 2500)
