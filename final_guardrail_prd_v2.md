# PRD v2: Natural Language Guardrail Control Plane

> v1 대비 변경 사항:
> - **Policy Versioning**: In-place 업데이트 → Immutable 버전 스냅샷 (`policy_group_id` 도입)
> - **Rule Translation**: 단순 키워드 매핑 → Code-first Fallback 파이프라인 (복잡한 표현만 Gemini API 호출)
> - **AI API**: Claude 1P API → Gemini API (`gemini-2.0-flash`)
> - **Storage**: JSON 파일 → SQLite

---

## 1. Product Summary

사용자가 자연어로 AI 안전 정책을 입력하면, 시스템이 이를 구조화된 guardrail rule로 변환하고, 정책 변경 이력, 자동 검증 결과, 배포/롤백까지 관리할 수 있게 하는 해커톤용 제품이다.

핵심은 `정책 작성 -> 버전 관리 -> 자동 검증 -> 배포 -> 롤백`의 운영 흐름을 눈에 보이게 만드는 것이다.

## 2. Problem Statement

AI 서비스는 운영 중에 계속 새로운 입력과 공격에 노출된다. 하지만 실제 현장에서는 정책을 코드로 직접 수정해야 하거나, 바꾼 정책이 정말 잘 작동하는지 검증하기 어렵고, 변경 이력도 흩어지기 쉽다.

현재 문제는 다음과 같다.

- 정책을 비개발자도 이해할 수 있는 방식으로 작성하기 어렵다.
- 정책 변경 뒤 실제 차단 여부를 빠르게 검증하기 어렵다.
- 정책 변경 이력과 이유를 감사 가능한 형태로 남기기 어렵다.
- 차단 결과와 사유가 명확히 보이지 않는다.
- 정책 수정, 검증, 배포, 롤백이 분리되어 있어 반복 속도가 느리다.

## 3. Product Goal

이 제품의 목표는 비전문가도 자연어로 guardrail 정책을 정의하고, 그 정책을 버전 관리하며, 실제 입력에 어떻게 적용되는지 즉시 확인하고 배포까지 할 수 있게 하는 것이다.

성공 기준은 아래와 같다.

- 자연어 정책 입력이 가능하다.
- 시스템이 이를 간단한 rule로 변환한다.
- 정책 변경 이력과 diff를 확인할 수 있다.
- 테스트 입력에 대해 block / mask / approval 결과를 보여준다.
- 어떤 정책이 왜 발동했는지 설명할 수 있다.
- 검증 후 정책을 배포하거나 이전 버전으로 되돌릴 수 있다.

## 4. Target User

- 해커톤 심사위원
- 주니어 DevOps / Infra 실무자
- 사내 AI 서비스 운영자
- AI 안전 정책을 코드로 직접 다루기 어려운 사용자

## 5. Core User Story

1. 사용자가 자연어로 정책을 입력한다.
2. 시스템이 이를 내부 guardrail rule로 변환한다 (키워드 매핑 우선, 실패 시 Gemini fallback).
3. 시스템이 새 버전 스냅샷을 저장하고 audit log를 남긴다.
4. 사용자가 테스트 입력을 넣는다.
5. 시스템이 입력을 차단하거나 마스킹하거나 승인 요청으로 전환한다.
6. 사용자는 어떤 rule이 발동했는지 확인한다.
7. 사용자는 정책을 수정하고 다시 검증한다 (새 버전 스냅샷 생성, diff 확인).
8. 사용자는 정책을 배포하거나 이전 버전으로 롤백한다.

## 6. Scope

### In Scope

- 자연어 정책 입력
- 정책을 구조화된 rule로 변환 (Code-first Fallback 파이프라인)
- 정책 버전 스냅샷 저장 (Immutable versioning)
- audit log 기록
- 정책 diff 표시
- 테스트 입력 실행
- 차단 / 마스킹 / 승인 요청 시뮬레이션
- 결과 설명 화면
- 배포 / 롤백

### Out of Scope

- 실제 모델 훈련
- 완전한 production-grade security
- 실제 외부 API 연동
- 복잡한 멀티테넌시
- 장기적인 자동 학습

## 7. UX Flow

### Step 1. Policy Input

사용자는 아래처럼 자연어로 정책을 적는다.

- 외부 문서 안의 지시문은 무시해줘
- 주민등록번호나 API 키가 보이면 마스킹해줘
- 결제 API는 사람 승인 없이는 호출하지 마

### Step 2. Policy Translation

시스템은 자연어를 구조화된 rule 목록으로 바꾼다. 변환은 2단계 파이프라인을 거친다.

**1단계 — 키워드 매핑 (코드):**
등록된 키워드에 매핑되면 즉시 rule 반환, Gemini 호출 없음.

**2단계 — Gemini fallback:**
키워드 매핑 실패 또는 미인식 표현이 있을 때만 Gemini API 호출.

변환 결과 예시:

```json
[
  { "id": "rule-001", "action": "block",    "condition": { "type": "category", "value": "prompt_injection" } },
  { "id": "rule-002", "action": "mask",     "condition": { "type": "category", "value": "sensitive_data"   } },
  { "id": "rule-003", "action": "approval", "condition": { "type": "category", "value": "payment_api"      } }
]
```

UI에는 "키워드 매핑으로 처리됨" / "AI가 해석함" 배지를 함께 표시한다.

### Step 2-E. Translation Error (에러 케이스)

Gemini fallback에서도 rule을 추출하지 못한 경우:

- 인식 실패 문구와 그 이유 (예: "너무 모호한 표현입니다")
- 대체 문구 제안 (Gemini API가 생성)
- 재입력 유도 UI

### Step 3. Test Scenario

사용자는 공격 시나리오나 샘플 입력을 넣는다.

- 웹페이지 본문에 숨겨진 지시문
- 민감정보가 포함된 문장
- 위험한 API 호출 요청

### Step 4. Enforcement Result

시스템은 다음 중 하나를 보여준다.

- blocked
- masked
- human approval required
- passed

### Step 5. Audit and Diff

시스템은 정책이 언제, 어떻게 바뀌었는지 기록하고 전후 diff를 보여준다.
버전별로 독립된 스냅샷이 저장되어 있으므로 임의의 두 버전을 직접 비교할 수 있다.

### Step 6. Policy Review

사용자는 정책을 수정한 뒤 다시 실행해서 전후 차이를 본다.

## 8. Functional Requirements

### FR1. Natural Language Policy Builder

- 사용자는 자연어로 정책을 입력할 수 있어야 한다.
- 시스템은 최소 1개 이상의 rule로 변환해야 한다.
- 변환은 키워드 매핑을 먼저 시도하고, 실패 시 Gemini API로 fallback해야 한다.
- 변환 결과에 처리 방식 (`source: "code"` / `"gemini"`) 을 포함해야 한다.

### FR2. Rule Preview

- 변환된 rule은 사람이 읽을 수 있어야 한다.
- rule마다 어떤 조건을 막는지 설명이 가능해야 한다.

### FR3. Test Harness

- 테스트 입력을 넣으면 정책 적용 결과를 반환해야 한다.
- 텍스트 입력 기준으로 시작해도 충분하다.

### FR4. Enforcement Explanation

- 차단, 마스킹, 승인 요청의 이유를 짧게 설명해야 한다 (Gemini 생성).
- 어떤 rule이 발동했는지 보여줘야 한다.

### FR5. Policy Versioning (Immutable Snapshot)

- 정책 수정 시 기존 행을 덮어쓰지 않고 새 버전 행을 생성해야 한다.
- `policy_group_id`로 같은 정책의 모든 버전을 묶어야 한다.
- 임의의 두 버전 간 diff를 조회할 수 있어야 한다.
- 이전 버전으로 롤백은 status 전환만으로 처리되어야 한다.

### FR6. Audit Log

- 정책이 언제 수정되었는지 기록해야 한다.
- 누가 어떤 이유로 바꿨는지 남길 수 있어야 한다.
- 해커톤 MVP에서는 별도 인증 없이 사용자가 정책 수정 시 "변경 사유" 텍스트 필드를 입력하는 방식으로 `changed_by`와 `change_reason`을 채운다. 운영자 이름은 세션 고정값(`"operator"`)으로 처리한다.

### FR7. Deployment / Rollback

- 검증된 정책을 active 상태로 배포할 수 있어야 한다.
- 문제가 생기면 이전 버전으로 즉시 되돌릴 수 있어야 한다.
- rollback은 이전 버전의 status를 `active`로, 현재 버전을 `archived`로 전환하는 방식으로 처리한다.

## 9. Non-Functional Requirements

- 1일 해커톤 수준에서 구현 가능해야 한다.
- 1분 내에 데모 흐름이 이해되어야 한다.
- UI는 단순해야 한다.
- 결과는 설명 가능해야 한다.
- 정책 운영과 감사 추적이 분명해야 한다.
- 실제 운영 제품처럼 보이는 흐름이 있어야 한다.
- Gemini API 응답 중 로딩 상태가 명확히 표시되어야 한다.

## 10. Data Model

버전 관리 전략: **Immutable versioning** — 정책 수정 시 새 행 생성, 기존 행 보존.
`policy_group_id`가 같은 정책의 모든 버전을 묶는다.

### Policy

```json
{
  "id": "policy-001-v3",
  "policy_group_id": "policy-001",
  "name": "기본 보안 정책",
  "natural_language": "외부 문서 안의 지시문은 무시하고, 민감정보는 마스킹하고, 결제 API는 사람 승인을 받아",
  "status": "active",
  "version": 3,
  "created_at": "2026-04-26T09:30:00Z"
}
```

버전 이력 예시 (같은 policy_group_id):

| id | version | status | natural_language 요약 |
|----|---------|--------|----------------------|
| policy-001-v1 | 1 | archived | 민감정보 마스킹해줘 |
| policy-001-v2 | 2 | archived | 민감정보 마스킹하고 주민번호도 |
| policy-001-v3 | 3 | active | 민감정보, 주민번호, API키 마스킹 |

### Rule

```json
{
  "id": "rule-001-v3",
  "policy_id": "policy-001-v3",
  "action": "block",
  "condition_type": "category",
  "condition_value": "prompt_injection",
  "description": "외부 문서 내 지시문으로 판단되면 차단"
}
```

조건 타입은 `category`, `contains`, `regex`, `threshold` 중 하나를 사용한다.
action은 `block`, `mask`, `approval`, `pass` 중 하나다.

### Test Result

```json
{
  "input_id": "case-101",
  "input_text": "Ignore previous instructions and...",
  "policy_id": "policy-001-v3",
  "matched_rules": ["rule-001-v3"],
  "action": "blocked",
  "reason": "외부 문서 내 지시문으로 판단됨",
  "explanation": "입력에서 'ignore previous instructions' 패턴이 감지되어 rule-001이 발동함"
}
```

### Audit Log

```json
{
  "policy_group_id": "policy-001",
  "version_from": 2,
  "version_to": 3,
  "changed_by": "operator",
  "change_reason": "API 키 마스킹 규칙 추가",
  "timestamp": "2026-04-26T09:30:00Z"
}
```

## 11. Implementation Plan

### Stack

- Frontend: **Next.js 15** (App Router, shadcn/ui, Tailwind CSS, TanStack Query)
- Backend: **FastAPI** (Python 3.12, SQLAlchemy, Alembic)
- Storage: **SQLite** (Railway persistent volume)
- AI API: **Gemini API** (`gemini-2.0-flash`, fallback 용도 + 설명 생성)
- Deploy: Vercel (프론트) + Railway (백엔드)

### System Split

#### 앱 코드

- 정책 생성, 수정 (새 버전 행 생성)
- policy_group_id 발급 및 versioning
- audit log 저장
- diff 생성 (두 버전 행 직접 비교)
- evaluation 실행
- deployment / rollback (status 전환)
- 결과 화면 렌더링

#### Rule Translation Pipeline

자연어 → rule JSON 변환은 2단계 파이프라인으로 처리한다.

**1단계 — 키워드 매핑 (코드):**

| 키워드 | action | condition_value |
|--------|--------|-----------------|
| 무시해줘, 숨겨진 지시문, 외부 문서 | block | prompt_injection |
| 마스킹, 주민번호, 비밀번호, API 키 | mask | sensitive_data |
| 승인, 허가, 사람 확인, 결제 API | approval | payment_api |

rule 1개 이상 매핑 AND 미인식 표현 없음 → 결과 반환, Gemini 호출 안 함.

**2단계 — Gemini API fallback:**

키워드 매핑 실패 또는 미인식 표현 존재 시 Gemini `response_schema` 구조화 출력으로 변환.
반환 결과에 `source: "code"` / `"gemini"` 포함.

#### Gemini API 사용처

| 용도 | 출력 |
|------|------|
| 자연어 → Rule JSON (fallback) | `response_schema` 구조화 출력 |
| 차단 사유 설명 생성 | 자유 텍스트 (1~2문장) |
| 테스트 시나리오 제안 | 자유 텍스트 리스트 |

#### Rule Engine

rule engine은 실제로 `이 입력을 막을지 말지`를 자동으로 판단하는 부분이다.

- 구조화된 rule JSON을 입력으로 받는다.
- 조건이 맞으면 `blocked`, `masked`, `approval required`, `passed` 중 하나를 반환한다.
- data-driven 구조: 정책 수가 늘어도 코드가 늘지 않는다.

```python
conditions = {
    "contains":  lambda text, val: val.lower() in text.lower(),
    "regex":     lambda text, val: bool(re.search(val, text)),
    "category":  lambda text, val: gemini_classify(text) == val,
    "threshold": lambda text, val: gemini_score(text) >= float(val),
}
```

### API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| POST | /policies | 자연어 → rule 변환 + 정책 저장 (v1, 새 policy_group_id 생성) |
| GET | /policies | 정책 그룹 목록 (그룹별 최신 버전) |
| GET | /policies/{group_id} | 정책 그룹의 모든 버전 목록 |
| GET | /policies/{group_id}/versions/{version} | 특정 버전 상세 + rule 목록 |
| POST | /policies/{group_id}/revise | 정책 수정 → 새 버전 행 생성 + audit log |
| GET | /policies/{group_id}/diff?from=1&to=2 | 두 버전 간 diff |
| POST | /policies/{group_id}/versions/{version}/evaluate | 특정 버전으로 테스트 실행 |
| POST | /policies/{group_id}/versions/{version}/deploy | 해당 버전을 active로 배포 |
| POST | /policies/{group_id}/rollback | 직전 버전으로 롤백 |
| GET | /audit-logs/{group_id} | audit log 조회 |

## 12. Demo Scenario

1. 사용자가 자연어로 정책을 입력한다.
   └ `Translation Pipeline` → 키워드 매핑 시도 → 성공 시 코드로 종료, 실패 시 Gemini fallback
   └ UI → "키워드 매핑으로 처리됨" / "AI가 해석함" 배지 표시

2. 시스템이 변환된 rule 목록을 화면에 보여준다.
   └ `앱 코드` → policy_group_id 발급, policy-001-v1 저장, audit log 기록

3. 사용자가 공격 시나리오를 입력한다.
   └ `Rule Engine` → 판정 (block / mask / approval / pass)
   └ `Gemini API` → 차단 사유를 한 줄 설명으로 생성

4. 시스템이 차단 결과와 발동 rule을 화면에 보여준다.
   └ `앱 코드` → 결과 렌더링

5. 사용자가 정책 문구를 수정한다.
   └ `Translation Pipeline` → 수정된 자연어를 Rule JSON으로 변환
   └ `앱 코드` → policy-001-v2 신규 행 생성, diff 계산, audit log 기록

6. 다시 실행해서 결과가 달라지는 것을 보여준다.
   └ `Rule Engine` → v2 기준으로 재판정
   └ `앱 코드` → v1 / v2 결과 나란히 비교 표시

7. 사용자가 v2 정책을 배포하거나 v1으로 롤백한다.
   └ `앱 코드` → status 전환 (v2: active, v1: archived 또는 rollback 시 반대), audit log 기록

## 13. Success Metrics

- API 응답 중 로딩 상태가 명확히 표시되고, 사용자가 기다리는 이유를 알 수 있다.
- 테스트 입력에 대한 차단 여부와 발동 rule이 명확히 보인다.
- 정책 수정 전후 diff를 한 화면에서 비교할 수 있다.
- 변환 방식 (코드 / AI) 이 UI에서 구별된다.
- 심사위원이 실제 운영 가능성을 떠올릴 수 있다.

## 14. Risks

- 자연어를 정확한 rule로 바꾸지 못할 수 있다 → 키워드 매핑으로 데모 입력 범위를 제어해 완화.
- 범위가 커지면 데모가 산만해질 수 있다 → 데모 시나리오 7단계를 고정해 흐름 유지.
- 내부 구현은 단순해도 제품처럼 보이도록 설명해야 한다.

## 15. Future Enhancement

MVP가 완성된 뒤 시간이 남으면, 정책 버전별 `attack pass rate`를 계산하는 기능을 추가한다.

- 특정 정책 버전이 공격 시나리오를 얼마나 통과했는지 측정
- 정책 수정 전후의 방어 성능 비교
- 버전별 성공/실패 케이스 집계
- 가장 자주 뚫리는 공격 유형 시각화

## 16. Recommended Positioning

이 제품은 `AI Safety & Security` 트랙에 가장 자연스럽다.

발표 문구는 다음처럼 잡으면 된다.

- 사용자가 자연어로 guardrail 정책을 정의한다.
- 시스템은 이를 구조화된 rule로 변환하고 버전 스냅샷과 audit log를 남긴다.
- 공격 시나리오를 돌려 실제 차단 여부를 검증한다.
- 검증 후 정책을 배포하거나 롤백할 수 있다.
