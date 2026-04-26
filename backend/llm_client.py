import json
import os
from pathlib import Path
from typing import Optional, List
from dotenv import load_dotenv
from google import genai

load_dotenv(dotenv_path=str(Path(__file__).parent.parent / ".env"))

_client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
MODEL = "gemini-2.0-flash"

_BASE_RULE_FORMAT = """Each rule must be a JSON object with:
- "action": one of "block", "mask", "approval", "pass"
- "condition": object with "type" (one of "category", "contains", "regex") and "value"
  - For category use one of: "prompt_injection", "sensitive_data", "payment_api", "unsafe_action"
  - For contains/regex: use the literal pattern string
- "description": short Korean explanation of what this rule does

Return ONLY a JSON array. No markdown fences, no explanation, just the JSON array."""

_PROMPTS_BY_TYPE = {
    "prompt_defense": _BASE_RULE_FORMAT + """

You are a prompt-injection defense specialist. Convert the user's policy into structured rules that detect adversarial inputs attempting to override AI instructions.

Focus on:
- Attempts to ignore/override/forget instructions → block + category:prompt_injection
- Role-play or identity-change attacks ("act as", "you are now") → block + category:prompt_injection
- System prompt extraction attempts → block + contains/regex
- Indirect injection via documents/URLs → block + category:prompt_injection

User policy:
{natural_language}""",

    "sensitive_data": _BASE_RULE_FORMAT + """

You are a sensitive data protection specialist. Convert the user's policy into rules that detect and mask PII, credentials, and financial data in AI outputs.

Focus on:
- Korean resident registration numbers (주민번호) → mask + regex:\\d{6}-\\d{7}
- Credit card numbers → mask + category:sensitive_data
- API keys, passwords, secret tokens → mask + category:sensitive_data
- Personal contact info (email, phone) → mask + regex patterns

User policy:
{natural_language}""",

    "content_safety": _BASE_RULE_FORMAT + """

You are a content safety specialist. Convert the user's policy into rules that detect harmful, unethical, or dangerous content in both user inputs and AI responses.

Focus on:
- Hate speech, harassment → block + contains/regex for slurs/threats
- Dangerous system commands (rm -rf, DROP TABLE) → block + category:unsafe_action
- Instructions for harmful activities → block + contains/regex
- Self-harm or violence promotion → block + contains/regex

User policy:
{natural_language}""",

    "compliance": _BASE_RULE_FORMAT + """

You are a legal and compliance specialist. Convert the user's policy into rules that enforce business rules, regulatory requirements, and approval workflows.

Focus on:
- Payment/financial operations requiring approval → approval + category:payment_api
- Professional advice (medical, legal, financial) → approval + contains/regex
- Age-restricted content checks → block/approval + contains/regex
- Regulated API access controls → approval + category:payment_api

User policy:
{natural_language}""",
}

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


def translate_natural_language(natural_language: str, policy_type: str = "content_safety") -> dict:
    template = _PROMPTS_BY_TYPE.get(policy_type, _PROMPTS_BY_TYPE["content_safety"])
    prompt = template.format(natural_language=natural_language)
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
