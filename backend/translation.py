from typing import List

_KEYWORD_MAP = [
    (
        ["무시해줘", "숨겨진 지시문", "외부 문서", "지시문", "프롬프트 인젝션", "인젝션",
         "ignore", "jailbreak", "system prompt", "이전 지시", "역할 무시"],
        "block", "category", "prompt_injection",
        "외부 지시문 또는 프롬프트 인젝션으로 판단되면 차단",
    ),
    (
        ["마스킹", "주민번호", "비밀번호", "api 키", "api키", "카드번호", "개인정보", "민감정보",
         "숨겨줘", "가려줘", "노출 금지", "보호", "암호화"],
        "mask", "category", "sensitive_data",
        "민감 정보(주민번호, API 키 등)가 감지되면 마스킹",
    ),
    (
        ["승인", "허가", "사람 확인", "결제 api", "결제api", "사람이 확인", "직접 확인",
         "결제", "payment", "청구", "charge", "billing", "구매", "환불"],
        "approval", "category", "payment_api",
        "결제 관련 작업은 사람 승인 필요",
    ),
    (
        ["시스템 종료", "rm -rf", "drop table", "unsafe", "위험한 명령",
         "삭제 명령", "db 삭제", "포맷", "shutdown", "reboot"],
        "block", "category", "unsafe_action",
        "위험한 시스템 명령으로 판단되면 차단",
    ),
]


def keyword_translate(natural_language: str) -> dict:
    text = natural_language.lower()
    matched_values: set = set()
    rules: List[dict] = []

    for keywords, action, cond_type, cond_value, description in _KEYWORD_MAP:
        if cond_value in matched_values:
            continue
        if any(kw in text for kw in keywords):
            matched_values.add(cond_value)
            rules.append({
                "action": action,
                "condition_type": cond_type,
                "condition_value": cond_value,
                "description": description,
            })

    success = len(rules) > 0
    return {"rules": rules, "success": success, "source": "code"}


def translate(natural_language: str) -> dict:
    result = keyword_translate(natural_language)
    if result["success"]:
        return result

    from llm_client import translate_natural_language
    llm = translate_natural_language(natural_language)
    return {**llm, "source": "gemini"}
