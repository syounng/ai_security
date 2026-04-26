# Natural Language Guardrail Control Plane
### AI 안전 정책 관리 시스템 — 설계 및 구현

---

## 목차

1. 가드레일 모델 분리 설계
2. 폴백 구조
3. Audit Log
4. Rule Engine

---

## 1. 가드레일 모델 분리 설계

### 왜 단일 모델로 만들지 않았는가?

> "다른 리스크는 다른 판단 기준을 요구한다."
> — Kakao Kanana Safeguard 설계 원칙

단일 LLM 파이프라인이 모든 리스크를 처리할 경우 세 가지 문제가 발생한다.

| 문제 | 설명 |
|---|---|
| **판단 기준 희석** | 프롬프트 인젝션 탐지와 PII 마스킹은 판단 방식 자체가 다름. 하나의 프롬프트에 섞이면 둘 다 부정확해진다 |
| **번역 품질 저하** | 전문화된 도메인 지식 없이 범용 프롬프트로 룰을 생성하면 엣지 케이스를 놓치기 쉽다 |
| **유지보수 난이도** | 프롬프트 하나를 수정하면 모든 유형의 정책에 영향을 줘 사이드 이펙트를 예측하기 어렵다 |

---

### 4종 정책 유형

```
사용자 입력 ──→ [Rule Engine 판정] ──→ 결과
                      │
              ┌───────┴────────┐
              │  policy_type   │
              ├───────────────────── prompt_defense  → 지시문 무시·역할극 탐지
              ├───────────────────── sensitive_data  → PII·결제정보 마스킹
              ├───────────────────── content_safety  → 유해 콘텐츠 차단
              └───────────────────── compliance      → 규정 준수·승인 요청
```

| 정책 유형 | 탐지 대상 | 주요 액션 | 전문 번역 프롬프트 |
|---|---|---|---|
| `prompt_defense` | 지시문 무시, 역할극 공격, 시스템 프롬프트 유출 | block | prompt-injection defense specialist |
| `sensitive_data` | 주민번호, 카드번호, API 키, 이메일 | mask | sensitive data protection specialist |
| `content_safety` | 유해 명령어, 혐오 발언, 위험 콘텐츠 | block | content safety specialist |
| `compliance` | 결제 API, 의료·법률 자문, 규정 위반 | approval | legal and compliance specialist |

---

### 분리 설계의 이점

**① 전문화된 LLM 번역 프롬프트**

자연어 정책을 룰로 변환할 때, 정책 유형별로 다른 system prompt를 사용한다.

```
[prompt_defense 전용 프롬프트]
"You are a prompt-injection defense specialist.
 Focus on: ignore/override instructions → block + category:prompt_injection
           role-play identity attacks → block + category:prompt_injection"

[sensitive_data 전용 프롬프트]
"You are a sensitive data protection specialist.
 Focus on: 주민번호 pattern → mask + regex:\d{6}-\d{7}
           API keys, passwords → mask + category:sensitive_data"
```

→ 동일한 자연어 입력도 유형에 따라 더 정확한 룰로 변환된다.

**② 사이드 이펙트 격리**

`sensitive_data` 정책의 번역 프롬프트를 수정해도 `prompt_defense` 정책 번역에는 영향이 없다. 유형별로 독립된 프롬프트 템플릿을 관리하므로 변경 범위가 명확하다.

---

## 2. 폴백 구조

### 왜 폴백이 필요한가?

가드레일 시스템에서 평가 실패나 번역 실패는 **서비스 중단이 아닌 안전한 기본값으로 처리**되어야 한다. 모든 에러가 사용자에게 노출되거나 시스템을 멈추게 하면 안 된다.

---

### 4단계 폴백 구조

#### ① LLM 번역 실패 → 재표현 제안

```python
# backend/main.py
result = translation.translate(req.natural_language)

if not result["success"]:
    suggestion = llm_client.suggest_rephrasing(req.natural_language)
    raise HTTPException(422, detail={
        "error": "번역 실패",
        "suggestion": suggestion   # ← Gemini가 더 명확한 표현을 제안
    })
```

자연어가 너무 모호하거나 룰로 변환 불가능할 때, 단순 에러가 아닌 **개선된 표현을 제안**한다. 사용자는 제안 문구를 한 번의 클릭으로 바로 적용할 수 있다.

```
[UI]
변환 실패: Empty result from LLM
제안: "외부 문서에 포함된 지시문은 무시하고,
      시스템 역할 변경 시도는 차단해줘"  [이 문구 사용 →]
```

---

#### ② Rule Engine 미탐지 → Gemini 2차 안전 판정

```python
# backend/main.py
result = rule_engine.evaluate(req.input_text, rules)

# 룰에 아무것도 안 걸린 경우 Gemini 2차 안전 판정
if result["action"] == "passed" and not result["matched_rules"]:
    judge = llm_client.safety_judge(req.input_text)
    return TestResult(
        action=judge["action"],
        explanation=judge["reason"],
        translation_source="gemini",   # ← 처리 경로 표시
    )
```

정의된 룰이 아무것도 매치하지 않아도, 입력이 완전히 무해하다고 확신할 수 없다. Rule Engine이 놓친 새로운 패턴의 공격을 **Gemini가 의미론적으로 2차 판정**한다. UI에 "✨ Gemini API" 배지로 처리 경로가 표시된다.

---

#### ③ policy_type 미인식 → content_safety로 대체

```python
# backend/llm_client.py
template = _PROMPTS_BY_TYPE.get(policy_type, _PROMPTS_BY_TYPE["content_safety"])
# ↑ 알 수 없는 type이 들어와도 가장 범용적인 content_safety 프롬프트로 처리
```

미래에 새로운 policy_type이 추가되거나 데이터 마이그레이션 과정에서 알 수 없는 타입이 들어와도 **시스템이 안전하게 동작**한다.

---

#### ④ Gemini API 장애 → 기본 메시지로 대체

```python
# backend/llm_client.py
def generate_explanation(...) -> str:
    try:
        resp = _client.models.generate_content(...)
        return resp.text.strip()
    except Exception:
        # Gemini API 장애 시 룰 정보를 이용한 기본 메시지 반환
        return f"'{matched_text}' 패턴이 감지되어 {action} 처리되었습니다."
```

AI 설명 생성이 실패해도 **평가 결과(block/mask/pass)는 영향받지 않는다**. 룰 엔진의 판정은 이미 완료되어 있으므로 설명 문구만 기본값으로 대체된다.

---

### 폴백 구조 요약

```
자연어 입력
    │
    ▼
LLM 번역 시도 ──[실패]──→ 재표현 제안 (422 + suggestion)
    │
    ▼ [성공]
룰 저장 / 정책 생성
    │
    ▼
평가 요청 (input_text)
    │
Rule Engine 판정
    │
    ├─ [매치 있음] → Gemini 한국어 설명 생성
    │                 └─ Gemini 장애 시 → 기본 메시지로 대체
    │
    └─ [매치 없음] → Gemini 2차 안전 판정
                      └─ policy_type 미인식 시 → content_safety로 폴백
```

---

## 3. Audit Log

### 왜 만들었는가?

가드레일 정책은 **보안 인프라**다. 언제, 누가, 왜 정책을 바꿨는지 기록이 없으면 세 가지 문제가 생긴다.

| 문제 상황 | Audit Log 없을 때 | Audit Log 있을 때 |
|---|---|---|
| 장애 발생 | "언제 정책이 바뀌었나?" 알 수 없음 | 변경 시점과 변경 내용 즉시 확인 |
| 규정 감사 | 변경 이력 재구성 불가 | 전체 이력 제출 가능 |
| 롤백 판단 | 이전 상태 알 수 없음 | version_from/to로 변경 범위 파악 |

---

### 설계: Append-only JSONL

```python
# backend/audit.py — 추가만 가능, 수정/삭제 불가
def append(entry: AuditEntry) -> None:
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")
```

**JSONL(JSON Lines)** 형식을 선택한 이유:
- 한 줄 = 한 이벤트 → 파일 append만으로 기록 (별도 DB 불필요)
- 기존 레코드를 덮어쓸 수 없는 구조 → 무결성 보장
- 줄 단위로 읽으므로 대용량에도 메모리 효율적

---

### 기록되는 이벤트

```jsonl
{"policy_group_id":"grp-abc123","policy_name":"프롬프트 인젝션 방어","version_from":null,"version_to":1,"changed_by":"operator","change_reason":"최초 생성","timestamp":"2026-04-26T05:42:03Z"}
{"policy_group_id":"grp-abc123","policy_name":"프롬프트 인젝션 방어","version_from":1,"version_to":1,"changed_by":"operator","change_reason":"배포 (active 전환)","timestamp":"2026-04-26T05:42:32Z"}
{"policy_group_id":"grp-abc123","policy_name":"프롬프트 인젝션 방어","version_from":1,"version_to":2,"changed_by":"operator","change_reason":"위험 명령 차단 규칙 추가","timestamp":"2026-04-26T05:44:30Z"}
{"policy_group_id":"grp-abc123","policy_name":"프롬프트 인젝션 방어","version_from":2,"version_to":1,"changed_by":"operator","change_reason":"롤백","timestamp":"2026-04-26T05:46:12Z"}
```

| 필드 | 의미 |
|---|---|
| `policy_group_id` | 정책 그룹 식별자 (모든 버전 공유) |
| `version_from` | 변경 전 버전 (`null` = 최초 생성) |
| `version_to` | 변경 후 버전 |
| `change_reason` | 변경 이유 (사람이 직접 입력) |
| `changed_by` | 변경자 |

---

### 모든 상태 전환에서 자동 기록

```python
# 정책 생성, 수정, 배포, 롤백 — 모든 시점에 audit.record() 호출
@app.post("/policies/{group_id}/versions/{version}/deploy")
def deploy_policy(group_id: str, version: int, db: Session = Depends(get_db)):
    updated = storage.deploy_policy(db, policy_id)
    audit.record(                          # ← 빠짐없이 기록
        policy_group_id=group_id,
        change_reason="배포 (active 전환)",
    )
```

---

## 4. Rule Engine

### 작동 원리

룰 엔진은 LLM 없이 **순수 Python**으로 동작하는 결정적(deterministic) 평가기다. LLM이 생성한 룰을 실제로 실행하는 역할을 한다.

```
[사용자 입력 텍스트]
        │
        ▼
  정책의 모든 룰 순회
  (for rule in rules)
        │
   ┌────┴────────────────────┐
   │ condition_type 확인      │
   ├─ "category" → 카테고리 패턴 매칭 (미리 정의된 regex 목록)
   ├─ "contains" → 단순 문자열 포함 여부
   └─ "regex"    → 사용자 정의 정규식 매칭
        │
   [매치 발생 시]
   action 기록 + 우선순위 비교
        │
        ▼
   최고 우선순위 action 반환
   block(0) > approval(1) > mask(2) > pass(3)
```

---

### 우선순위 시스템

여러 룰이 동시에 매치될 때 가장 강한 액션이 우선된다.

```python
# backend/rule_engine.py
PRIORITY = {"block": 0, "approval": 1, "mask": 2, "pass": 3}

# 예: "주민번호를 rm -rf로 삭제해줘" 입력
# → rule1 (sensitive_data → mask, priority=2) 매치
# → rule2 (unsafe_action → block, priority=0) 매치
# → 최종 결과: block (0 < 2)
```

---

### 3가지 매처 (Matcher)

#### category — 내장 패턴 묶음

```python
CATEGORY_PATTERNS = {
    "prompt_injection": [
        r"ignore (previous|prior|above) instructions?",
        r"you are now",
        r"act as (a |an )?(?!assistant)",
        r"시스템 프롬프트",
        r"jailbreak",
        # ...
    ],
    "sensitive_data": [
        r"\d{6}-\d{7}",           # 주민번호
        r"\b\d{4}[\s-]\d{4}[\s-]\d{4}[\s-]\d{4}\b",  # 카드번호
        r"AIza[0-9A-Za-z\-_]{35}", # Google API Key
        r"sk-[a-zA-Z0-9]{48}",    # OpenAI Key
        # ...
    ],
    "payment_api": [...],
    "unsafe_action": [...],
}
```

LLM이 `category:prompt_injection` 룰을 생성하면, 위 패턴 목록 전체가 자동으로 적용된다. 새 공격 패턴은 카테고리에 추가하면 해당 카테고리를 사용하는 모든 정책에 즉시 반영된다.

#### contains — 단순 키워드 매칭

```python
def _match_contains(text: str, value: str) -> bool:
    return value.lower() in text.lower()
```

성능이 가장 빠르다. LLM이 `contains:의료 진단` 룰을 생성하면 입력에 "의료 진단"이 포함될 때 트리거된다.

#### regex — 사용자 정의 패턴

```python
def _match_regex(text: str, pattern: str) -> Optional[re.Match]:
    try:
        return re.search(pattern, text, re.IGNORECASE)
    except re.error:
        return None  # 잘못된 패턴은 무시하고 계속 진행
```

`\d{2,3}-\d{3,4}-\d{4}` (전화번호) 같은 세밀한 패턴을 LLM이 직접 생성한다.

---

### 데이터 구조

```
PolicyGroup (정책 그룹)
└── group_id: "grp-abc123"           ← 모든 버전이 공유하는 식별자

    Policy (정책 버전) — 불변 (Immutable)
    ├── id: "grp-abc123-v2"          ← group_id + version으로 구성
    ├── policy_group_id: "grp-abc123"
    ├── name: "프롬프트 인젝션 방어"
    ├── natural_language: "외부 문서의 지시문은 무시해줘..."   ← 사람이 작성
    ├── policy_type: "prompt_defense"
    ├── status: "active" | "draft" | "archived"
    └── version: 2

        Rule (룰) — Policy 1 : N
        ├── id: "rule-4d5a9c96"
        ├── policy_id: "grp-abc123-v2"
        ├── action: "block"                     ← 실행할 액션
        ├── condition_type: "category"          ← 매처 종류
        ├── condition_value: "prompt_injection" ← 매처 값
        └── description: "지시문 무시 시도 차단"  ← Gemini가 한국어로 설명 생성
```

**불변 버전 관리 (Immutable Versioning)**

정책 수정 시 기존 버전은 변경되지 않는다. 새 버전이 생성되며 기존 버전은 이력으로 보존된다.

```
그룹: grp-abc123 "프롬프트 인젝션 방어"
├── v1 (archived) → 룰 3개
├── v2 (active)   → 룰 4개  ← 현재 운영 중
└── v3 (draft)    → 룰 5개  ← 작업 중
```

배포(deploy)는 특정 버전을 active로 전환한다. 롤백(rollback)은 이전 버전을 다시 active로 만든다.

---

### 전체 흐름 요약

```
사람이 자연어 작성
        │
        ▼
   Gemini API
   (policy_type별 전문 프롬프트)
        │
        ▼
   Rule JSON 생성
   [{ action: "block", condition_type: "category", condition_value: "prompt_injection" }]
        │
        ▼
   SQLite DB 저장 (불변 버전으로)
        │
        ▼
   /evaluate 호출 시
   Rule Engine이 LLM 없이
   regex/contains/category로 즉시 판정
        │
        ├─ [매치 있음] → Gemini가 한국어 설명 생성
        │               "시스템 프롬프트 유출 시도가 감지되어 차단되었습니다."
        │
        └─ [매치 없음] → Gemini 2차 안전 판정
                         (의미론적 위험 여부 재검토)
        │
        ▼
   결과: blocked / masked / approval_required / passed
```

---

*Natural Language Guardrail Control Plane — 2026.04*
