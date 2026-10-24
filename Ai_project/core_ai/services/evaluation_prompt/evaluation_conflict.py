
from pathlib import Path
_JUDGE_PATH = Path(__file__).parent / "prompts" / "judge_conflict.txt"
if _JUDGE_PATH.exists():
    JUDGE_PROMPT = _JUDGE_PATH.read_text(encoding="utf-8")
else:
    JUDGE_PROMPT = "You are a conflict evaluation judge. Respond in JSON."

import json
import os
from typing import Dict, Any


class ConflictEvaluator:
    def __init__(self, provider: str = "openrouter", api_key: str = None, model: str = None):
       
        self.provider = provider.lower()
        
        if self.provider == "openrouter":
            self.base_url = "https://openrouter.ai/api/v1"
            
            # ====================== أفضل الموديلات المجانية 2026 ======================
            self.model = model or "qwen/qwen3-coder:free"          # الأفضل حالياً للكود والتحليل
            api_key = api_key or os.getenv("OPENROUTER_API_KEY")
            
        else:  # openai
            self.base_url = None
            self.model = model or "gpt-4o-mini"
            api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError(f"API Key is required for {provider.upper()}")

        from openai import OpenAI
        self.client = OpenAI(
            api_key=api_key,
            base_url=self.base_url if self.provider == "openrouter" else None
        )

    def evaluate(self, diagram_a: str, diagram_b: str, conflict_result: Any) -> Dict:
        """
        تقييم شبه آلي باستخدام LLM-as-a-Judge
        """
        if isinstance(conflict_result, dict):
            result_str = json.dumps(conflict_result, indent=2, ensure_ascii=False)
        else:
            result_str = str(conflict_result)

        prompt = JUDGE_PROMPT.format(
            diagram_a=diagram_a,
            diagram_b=diagram_b,
            conflict_result=result_str
        )

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a strict, professional, and fair code architecture judge."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1200
            )

            content = response.choices[0].message.content.strip()

            # تنظيف الـ JSON إذا وجدت markdown
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            evaluation = json.loads(content)
            return evaluation

        except Exception as e:
            print(f"[Judge Error] {e}")
            return {
                "overall_score": 0,
                "scores": {},
                "strengths": [],
                "weaknesses": ["Evaluation failed due to error"],
                "missed_conflicts": [],
                "comments": f"Error: {str(e)}",
                "final_verdict": "Error"
            }


# ====================== مثال استخدام ======================
if __name__ == "__main__":
    evaluator = ConflictEvaluator(
        provider="openrouter",
        model="qwen/qwen3-coder:free"        # أفضل موديل مجاني حالياً للكود
        # model="google/gemma-4-31b-it:free"
        # model="meta-llama/llama-3.3-70b-instruct:free"
    )

    result = evaluator.evaluate(
        diagram_a="... old diagram ...",
        diagram_b="... new diagram ...",
        conflict_result={"conflicts": [], "summary": "No conflicts"}
    )

    print(f"Overall Score: {result.get('overall_score')}%")
    print(f"Verdict: {result.get('final_verdict')}")






