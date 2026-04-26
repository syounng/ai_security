import json
import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from google import genai

load_dotenv(dotenv_path=str(Path(__file__).parent.parent / ".env"))

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.0-flash"

_NL_TO_RULES_PROMPT = """You are a security policy translator. Convert the user's natural language security policy into structured JSON rules.

Each rule must be a JSON object with these EXACT fields (flat, no nesting):
- "action": one of "block", "mask", "approval", "pass"
- "condition_type": one of "category", "contains", "regex"
- "condition_value": string
  - If condition_type is "category", use one of: "prompt_injection", "sensitive_data", "payment_api", "unsafe_action"
  - If condition_type is "contains" or "regex": use the literal pattern string
- "description": short Korean explanation of what this rule does

Return ONLY a JSON array. No markdown fences, no explanation, just the JSON array.

Mapping hints:
- "지시문 무시", "외부 문서", "프롬프트 인젝션", "jailbreak" → block + category:prompt_injection
- "주민번호", "카드번호", "API 키", "비밀번호", "마스킹", "개인정보" → mask + category:sensitive_data
- "결제", "payment", "청구", "승인", "허가" → approval + category:payment_api
- "시스템 종료", "rm -rf", "DB 삭제", "위험한 명령" → block + category:unsafe_action

Example output:
[
  {"action": "block", "condition_type": "category", "condition_value": "prompt_injection", "description": "프롬프트 인젝션 차단"},
  {"action": "mask", "condition_type": "category", "condition_value": "sensitive_data", "description": "민감정보 마스킹"}
]

User policy:
{natural_language}"""

_EXPLAIN_PROMPT = """A guardrail rule engine evaluated user input and took an action.

Input text: {input_text}
Action taken: {action}
Triggered rules: {matched_rules}
Matched snippet: {matched_text}

Write ONE sentence in Korean explaining why this action was taken. Be specific about what was detected. No preamble."""

_SUGGEST_PROMPT = """This security policy text could not be converted to rules:
"{failed_text}"

Suggest a clearer way to express this as a security policy in 1-2 Korean sentences.
Return only the suggested text."""


def translate_natural_language(natural_language: str) -> dict:
    prompt = _NL_TO_RULES_PROMPT.format(natural_language=natural_language)
    try:
        resp = _client.models.generate_content(model=MODEL, contents=prompt)
        text = resp.text.strip()
        if "```" in text:
            parts = text.split("```")
            text = parts[1] if len(parts) > 1 else parts[0]
            if text.startswith("json"):
                text = text[4:]
        rules_data = json.loads(text.strip())
        if not isinstance(rules_data, list) or len(rules_data) == 0:
            raise ValueError("Empty result from LLM")
        # normalize old nested condition format if Gemini ignores new prompt
        for r in rules_data:
            if "condition" in r and "condition_type" not in r:
                r["condition_type"] = r["condition"]["type"]
                r["condition_value"] = r["condition"]["value"]
                del r["condition"]
        return {"success": True, "rules": rules_data}
    except Exception as e:
        return {"success": False, "error": str(e), "rules": []}


def generate_explanation(
    input_text: str,
    action: str,
    matched_rules: List[str],
    matched_text: Optional[str],
) -> str:
    prompt = _EXPLAIN_PROMPT.format(
        input_text=input_text[:200],
        action=action,
        matched_rules=", ".join(matched_rules) if matched_rules else "없음",
        matched_text=matched_text or "N/A",
    )
    try:
        resp = _client.models.generate_content(model=MODEL, contents=prompt)
        return resp.text.strip()
    except Exception:
        snippet = matched_text or "입력"
        return f"'{snippet}' 패턴이 감지되어 {action} 처리되었습니다."


def suggest_rephrasing(failed_text: str) -> str:
    prompt = _SUGGEST_PROMPT.format(failed_text=failed_text[:300])
    try:
        resp = _client.models.generate_content(model=MODEL, contents=prompt)
        return resp.text.strip()
    except Exception:
        return "더 구체적인 조건으로 다시 입력해 주세요. 예: '주민번호가 포함된 입력은 마스킹해줘'"
