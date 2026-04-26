import re
from typing import Optional, List, Dict
from models import Rule

CATEGORY_PATTERNS: Dict[str, List[str]] = {
    "prompt_injection": [
        r"ignore (previous|prior|above) instructions?",
        r"disregard (previous|prior|above|all) instructions?",
        r"forget (everything|all|your instructions)",
        r"you are now",
        r"act as (a |an )?(?!assistant)",
        r"새로운 역할",
        r"이전 지시",
        r"지시문을 무시",
        r"시스템 프롬프트",
        r"system prompt",
        r"jailbreak",
        r"DAN mode",
    ],
    "sensitive_data": [
        r"\d{6}-\d{7}",
        r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",
        r"AIza[0-9A-Za-z\-_]{35}",
        r"sk-[a-zA-Z0-9]{48}",
        r"(password|passwd|비밀번호)\s*[:=]\s*\S+",
        r"api[_\s]?key\s*[:=]\s*\S+",
        r"secret[_\s]?key\s*[:=]\s*\S+",
    ],
    "payment_api": [
        r"결제\s*(api|호출|실행|처리)",
        r"pay(ment)?\s*api",
        r"charge\s*(card|user|account)",
        r"billing\s*api",
        r"트랜잭션\s*실행",
        r"카드\s*결제",
    ],
    "unsafe_action": [
        r"(delete|drop|truncate)\s+(table|database|db)",
        r"rm\s+-rf",
        r"shutdown|reboot|halt",
        r"sudo\s+",
        r"시스템\s*(종료|삭제|포맷)",
    ],
}

PRIORITY = {"block": 0, "approval": 1, "mask": 2, "pass": 3}
ACTION_MAP = {"block": "blocked", "mask": "masked", "approval": "approval_required", "pass": "passed"}


def _match_category(text: str, category: str) -> Optional[re.Match]:
    for pattern in CATEGORY_PATTERNS.get(category, []):
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return m
    return None


def _match_contains(text: str, value: str) -> bool:
    return value.lower() in text.lower()


def _match_regex(text: str, pattern: str) -> Optional[re.Match]:
    try:
        return re.search(pattern, text, re.IGNORECASE)
    except re.error:
        return None


def evaluate(input_text: str, rules: List[Rule]) -> dict:
    best_action = "pass"
    best_priority = PRIORITY["pass"]
    matched_rule_ids: List[str] = []
    matched_text: Optional[str] = None

    for rule in rules:
        match = None
        cond_type = rule.condition_type
        cond_value = rule.condition_value

        if cond_type == "category":
            match = _match_category(input_text, cond_value)
        elif cond_type == "contains":
            if _match_contains(input_text, cond_value):
                match = True
        elif cond_type == "regex":
            match = _match_regex(input_text, cond_value)

        if match:
            matched_rule_ids.append(rule.id)
            if isinstance(match, re.Match) and matched_text is None:
                matched_text = match.group(0)
            p = PRIORITY.get(rule.action, PRIORITY["pass"])
            if p < best_priority:
                best_priority = p
                best_action = rule.action

    return {
        "action": ACTION_MAP[best_action],
        "matched_rules": matched_rule_ids,
        "matched_text": matched_text,
    }
