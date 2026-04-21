import requests
import time
import json
import hashlib
from datetime import datetime, timedelta
from django.conf import settings
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    """
    Enhanced version of GeminiClient with advanced rate limiting handling
    """
    
    MAX_RETRIES = 5  # Increased retries for free models (may be slower)
    BASE_WAIT_TIME = 30  # Wait 30 seconds on rate limit (less than paid models)
    CACHE_TIMEOUT = 3600 * 48  # Cache for 48 hours (free models are more stable)
    
    @staticmethod
    def _generate_cache_key(system_prompt, user_prompt):
        """توليد مفتاح cache فريد للطلب"""
        combined = f"{system_prompt}|{user_prompt}"
        return f"llm_response_{hashlib.md5(combined.encode()).hexdigest()}"
    
    @staticmethod
    def _get_cached_response(cache_key):
        """الحصول على استجابة محفوظة من cache"""
        try:
            cached = cache.get(cache_key)
            if cached:
                logger.info(f"[LLM Cache] Found cached response for key: {cache_key[:20]}...")
                return cached
        except Exception as e:
            logger.warning(f"[LLM Cache] Error getting cached response: {e}")
        return None
    
    @staticmethod
    def _cache_response(cache_key, response):
        """حفظ الاستجابة في cache"""
        try:
            cache.set(cache_key, response, LLMClient.CACHE_TIMEOUT)
            logger.info(f"[LLM Cache] Cached response for key: {cache_key[:20]}...")
        except Exception as e:
            logger.warning(f"[LLM Cache] Error caching response: {e}")
    
    @staticmethod
    def _check_rate_limit_status():
        """فحص حالة rate limit الحالية"""
        rate_limit_key = "openrouter_rate_limit_status"
        status = cache.get(rate_limit_key)
        
        if status and status.get('blocked_until'):
            blocked_until = datetime.fromisoformat(status['blocked_until'])
            if datetime.now() < blocked_until:
                remaining_time = (blocked_until - datetime.now()).total_seconds()
                return False, remaining_time
        
        return True, 0
    
    @staticmethod
    def _set_rate_limit_block(duration_minutes=60):
        """تسجيل حالة rate limit block"""
        rate_limit_key = "openrouter_rate_limit_status"
        blocked_until = datetime.now() + timedelta(minutes=duration_minutes)
        
        cache.set(rate_limit_key, {
            'blocked_until': blocked_until.isoformat(),
            'blocked_at': datetime.now().isoformat()
        }, duration_minutes * 60)
        
        logger.warning(f"[Rate Limit] Blocked API calls until {blocked_until}")
    
    @staticmethod
    def call_model(system_prompt, user_prompt, use_cache=True, force_request=False, model=None):
        """
        Call OpenRouter API with advanced rate limiting and fallback handling.

        Args:
            system_prompt: System prompt text
            user_prompt: User request
            use_cache: Use cache (default: True)
            force_request: Force request even if rate limited (default: False)
            model: Specific model to use (default: None = use current default)
        """
        
        if use_cache:
            cache_key = LLMClient._generate_cache_key(system_prompt, user_prompt)
            cached_response = LLMClient._get_cached_response(cache_key)
            if cached_response:
                return cached_response
        
        if not force_request:
            can_request, wait_time = LLMClient._check_rate_limit_status()
            if not can_request:
                raise Exception(f"API temporarily blocked due to rate limit. Remaining time: {int(wait_time/60)} minutes")
        
        api_key = getattr(settings, "OPENROUTER_API_KEY", None)
        if not api_key:
            raise Exception("API Key missing in settings!")
        
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "X-Title": "Software Documentation Agent",
            "HTTP-Referer": "http://localhost:8000"
        }
        
        if model is None:
            model = LLMClient.get_current_model()

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "max_tokens": 4000,
            "temperature": 0.7
        }
        
        last_error = None
        available_models = [m["model"] for m in LLMClient.get_available_free_models()]
        
        for attempt in range(LLMClient.MAX_RETRIES):
            try:
                logger.info(f"[LLM Request] Attempt {attempt + 1}/{LLMClient.MAX_RETRIES} using model: {model}")
                
                response = requests.post(url, headers=headers, json=payload, timeout=120)
                
                # Handle errors that require switching to another model
                if response.status_code in (429, 404):
                    status_code = response.status_code
                    reason = "rate limit (429)" if status_code == 429 else "model not available (404)"
                    logger.warning(f"[LLM Request] {reason} on attempt {attempt + 1} with model: {model}")
                    
                    # Try switching to next model in list
                    current_index = available_models.index(model) if model in available_models else 0
                    next_index = (current_index + 1) % len(available_models)
                    next_model = available_models[next_index]
                    
                    if next_model != model and attempt < LLMClient.MAX_RETRIES - 1:
                        logger.info(f"[LLM Request] Switching from {model} to {next_model}")
                        model = next_model
                        payload["model"] = model
                        cache.set("current_llm_model", model, 3600)
                        wait_time = 10 if status_code == 429 else 2
                        time.sleep(wait_time)
                        continue
                    
                    # All models exhausted
                    if status_code == 429:
                        LLMClient._set_rate_limit_block(60)
                        rate_info = {
                            'limit': response.headers.get('X-RateLimit-Limit', 'Unknown'),
                            'remaining': response.headers.get('X-RateLimit-Remaining', 'Unknown'),
                            'reset': response.headers.get('X-RateLimit-Reset', 'Unknown')
                        }
                        error_msg = f"Daily request limit exceeded ({rate_info['limit']} requests). "
                        error_msg += f"Remaining: {rate_info['remaining']}. "
                        error_msg += f"Last tried model: {model}. "
                        error_msg += "Please add credits or wait until midnight UTC."
                        raise Exception(error_msg)
                    else:
                        error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                        raise Exception(f"All models unavailable. Last API Error: {status_code} - {error_data}")
                
                if response.status_code != 200:
                    error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else response.text
                    raise Exception(f"API Error: {response.status_code} - {error_data}")
                
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                if use_cache:
                    LLMClient._cache_response(cache_key, content)
                
                logger.info(f"[LLM Request] Success on attempt {attempt + 1} with model: {model}")
                return content
                
            except requests.exceptions.RequestException as e:
                last_error = f"Network error: {str(e)}"
                logger.error(f"[LLM Request] Network error on attempt {attempt + 1}: {e}")
                
                if attempt < LLMClient.MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"[LLM Request] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                
            except Exception as e:
                last_error = str(e)
                logger.error(f"[LLM Request] Error on attempt {attempt + 1}: {e}")
                
                if "rate limit" in str(e).lower() or "429" in str(e):
                    raise e
                
                if attempt < LLMClient.MAX_RETRIES - 1:
                    wait_time = (attempt + 1) * 5
                    logger.info(f"[LLM Request] Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
        
        raise Exception(f"Failed to connect to API after {LLMClient.MAX_RETRIES} attempts. Last error: {last_error}")

    @staticmethod
    def get_rate_limit_info():
        """الحصول على معلومات rate limit الحالية"""
        try:
            api_key = getattr(settings, "OPENROUTER_API_KEY", None)
            if not api_key:
                return {"error": "API Key missing"}
            
            url = "https://openrouter.ai/api/v1/auth/key"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"خطأ {response.status_code}: {response.text}"}
                
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def test_model_connection():
        """
        Test model connection and get information
        """
        try:
            api_key = getattr(settings, "OPENROUTER_API_KEY", None)
            if not api_key:
                return {"error": "API Key missing in settings"}

            test_prompt = "Hello, just testing the connection. Respond with 'OK' only."
            result = LLMClient.call_model(
                "You are a helpful assistant.",
                test_prompt,
                use_cache=False,
                force_request=True
            )

            return {
                "status": "success",
                "model": LLMClient.get_current_model(),
                "response": result.strip(),
                "message": "Successfully connected to LLM!"
            }

        except Exception as e:
            return {
                "status": "error",
                "model": LLMClient.get_current_model(),
                "error": str(e),
                "message": "Failed to connect to LLM"
            }

    @staticmethod
    def get_available_free_models():
        """
        إرجاع قائمة بالنماذج المجانية المتاحة على OpenRouter (مُحدَّثة ومُتحقَّق منها)
        """
        return [
            {
                "model": "openai/gpt-oss-120b:free",
                "name": "OpenAI GPT OSS 120B",
                "description": "نموذج OpenAI المفتوح - 120B param - أداء فائق",
                "strengths": ["reasoning قوي", "tool use", "131K context", "مجاني"],
                "context": "131K tokens"
            },
            {
                "model": "nvidia/nemotron-nano-9b-v2:free",
                "name": "NVIDIA Nemotron Nano 9B V2",
                "description": "نموذج NVIDIA المجاني - سريع وفعال للمهام العامة",
                "strengths": ["سريع", "مجاني", "NVIDIA بنية", "جيد للكود"],
                "context": "32K tokens"
            },
            {
                "model": "google/gemma-3-27b-it:free",
                "name": "Gemma 3 (27B)",
                "description": "نموذج Google الكبير - أداء ممتاز",
                "strengths": ["سياق كبير", "دقة عالية", "متعدد المهام"],
                "context": "8K tokens"
            },
            {
                "model": "meta-llama/llama-3.3-70b-instruct:free",
                "name": "Meta Llama 3.3 (70B)",
                "description": "نموذج Meta العملاق - أقوى نموذج مجاني",
                "strengths": ["قوة هائلة", "سياق ضخم", "دقة فائقة"],
                "context": "8K tokens"
            },
            {
                "model": "meta-llama/llama-3.2-3b-instruct:free",
                "name": "Meta Llama 3.2 (3B)",
                "description": "نموذج Meta الخفيف والموثوق",
                "strengths": ["أداء ممتاز", "موثوقية", "متوفر مجاناً"],
                "context": "4K tokens"
            },
            {
                "model": "mistralai/mistral-7b-instruct:free",
                "name": "Mistral 7B",
                "description": "نموذج Mistral المتوازن - جيد للاستخدام العام",
                "strengths": ["أداء جيد", "استجابة سريعة", "موثوقية"],
                "context": "32K tokens"
            },
            {
                "model": "mistralai/devstral-small-2505:free",
                "name": "Mistral Devstral Small",
                "description": "نموذج Mistral للبرمجة - محسّن للكود",
                "strengths": ["متخصص للكود", "أداء محسن", "مجاني"],
                "context": "32K tokens"
            }
        ]

    @staticmethod
    def switch_model(model_name):
        """
        تبديل النموذج المستخدم (للاختبار والمقارنة)
        """
        valid_models = [m["model"] for m in LLMClient.get_available_free_models()]

        if model_name not in valid_models:
            raise ValueError(f"نموذج غير صحيح. النماذج المتاحة: {valid_models}")

        cache.set("current_llm_model", model_name, 3600)  # ساعة واحدة
        logger.info(f"تم تبديل النموذج إلى: {model_name}")

        return {
            "status": "success",
            "model": model_name,
            "message": f"تم تبديل النموذج إلى {model_name}"
        }

    @staticmethod
    def get_current_model():
        """
        الحصول على النموذج المستخدم حالياً
        """
        cached_model = cache.get("current_llm_model")
        if cached_model:
            return cached_model

        # الموديل الافتراضي
        return "openai/gpt-oss-120b:free"