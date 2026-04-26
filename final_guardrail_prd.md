# PRD: Natural Language Guardrail Control Plane

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
2. 시스템이 이를 내부 guardrail rule로 변환한다.
3. 시스템이 정책 버전을 저장하고 변경 diff와 audit log를 남긴다.
4. 사용자가 테스트 입력을 넣는다.
5. 시스템이 입력을 차단하거나 마스킹하거나 승인 요청으로 전환한다.
6. 사용자는 어떤 rule이 발동했는지 확인한다.
7. 사용자는 정책을 수정하고 다시 검증한다.
8. 사용자는 정책을 배포하거나 이전 버전으로 롤백한다.

## 6. Scope

### In Scope

- 자연어 정책 입력
- 정책을 구조화된 rule로 변환
- 정책 버전 저장
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

시스템은 자연어를 구조화된 rule 목록으로 바꾼다. 정책 하나는 여러 rule을 포함할 수 있다.

```json
[
  { "id": "rule-001", "action": "block",    "condition": { "type": "category", "value": "prompt_injection" } },
  { "id": "rule-002", "action": "mask",     "condition": { "type": "category", "value": "sensitive_data"   } },
  { "id": "rule-003", "action": "approval", "condition": { "type": "category", "value": "payment_api"      } }
]
```

변환이 실패하거나 인식되지 않는 표현이 포함된 경우, 시스템은 파싱 실패 메시지와 함께 어떤 부분이 처리되지 않았는지 알려준다. 사용자는 문구를 수정해 다시 시도할 수 있다.

### Step 2-E. Translation Error (에러 케이스)

자연어에서 rule을 추출하지 못한 경우 시스템은 아래를 보여준다.

- 인식 실패 문구와 그 이유 (예: "너무 모호한 표현입니다")
- 대체 문구 제안 (Claude 1P API가 생성)
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

### Step 6. Policy Review

사용자는 정책을 수정한 뒤 다시 실행해서 전후 차이를 본다.

## 8. Functional Requirements

### FR1. Natural Language Policy Builder

- 사용자는 자연어로 정책을 입력할 수 있어야 한다.
- 시스템은 최소 1개 이상의 rule로 변환해야 한다.

### FR2. Rule Preview

- 변환된 rule은 사람이 읽을 수 있어야 한다.
- rule마다 어떤 조건을 막는지 설명이 가능해야 한다.

### FR3. Test Harness

- 테스트 입력을 넣으면 정책 적용 결과를 반환해야 한다.
- 텍스트 입력 기준으로 시작해도 충분하다.

### FR4. Enforcement Explanation

- 차단, 마스킹, 승인 요청의 이유를 짧게 설명해야 한다.
- 어떤 rule이 발동했는지 보여줘야 한다.

### FR5. Policy Versioning

- 정책 수정 전후를 비교할 수 있어야 한다.
- 이전 정책으로 되돌릴 수 있어야 한다.

### FR6. Audit Log

- 정책이 언제 수정되었는지 기록해야 한다.
- 누가 어떤 이유로 바꿨는지 남길 수 있어야 한다.
- 해커톤 MVP에서는 별도 인증 없이 사용자가 정책 수정 시 "변경 사유" 텍스트 필드를 입력하는 방식으로 `changed_by`와 `change_reason`을 채운다. 운영자 이름은 세션 고정값(`"operator"`)으로 처리한다.

### FR7. Deployment / Rollback

- 검증된 정책을 active 상태로 배포할 수 있어야 한다.
- 문제가 생기면 이전 버전으로 즉시 되돌릴 수 있어야 한다.

## 9. Non-Functional Requirements

- 1일 해커톤 수준에서 구현 가능해야 한다.
- 1분 내에 데모 흐름이 이해되어야 한다.
- UI는 단순해야 한다.
- 결과는 설명 가능해야 한다.
- 정책 운영과 감사 추적이 분명해야 한다.
- 실제 운영 제품처럼 보이는 흐름이 있어야 한다.

## 10. Data Model

Policy는 여러 Rule을 가진다 (1:N). Rule은 실제 판정 로직의 단위이고, Policy는 그 Rule들의 묶음과 버전 메타데이터를 가진다.

### Policy

```json
{
  "id": "policy-001",
  "name": "기본 보안 정책",
  "natural_language": "외부 문서 안의 지시문은 무시하고, 민감정보는 마스킹하고, 결제 API는 사람 승인을 받아",
  "rule_ids": ["rule-001", "rule-002", "rule-003"],
  "status": "active",
  "version": 3,
  "created_at": "2026-04-26T08:00:00Z",
  "updated_at": "2026-04-26T09:30:00Z"
}
```

### Rule

```json
{
  "id": "rule-001",
  "policy_id": "policy-001",
  "action": "block",
  "condition": {
    "type": "category",
    "value": "prompt_injection"
  },
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
  "matched_rules": ["rule-001"],
  "action": "blocked",
  "reason": "외부 문서 내 지시문으로 판단됨",
  "explanation": "입력에서 'ignore previous instructions' 패턴이 감지되어 rule-001이 발동함"
}
```

### Audit Log

```json
{
  "policy_id": "policy-001",
  "version_from": 2,
  "version_to": 3,
  "changed_by": "operator",
  "change_reason": "외부 문서 지시문 차단 규칙 강화",
  "timestamp": "2026-04-26T09:30:00Z"
}
```

## 11. Implementation Plan

### Minimal Stack

- Frontend: **Next.js** (App Router, React 기반, Vercel 배포 최적화)
- Backend: **FastAPI** (Python, Claude API 연동 편의성, 비동기 처리)
- Policy storage: **JSON file** (해커톤 범위에서 DB 없이 충분)
- Audit log storage: **JSONL** (append-only, 구조 단순)
- Rule engine: keyword / pattern / condition matcher (Python)
- Demo data: 미리 만든 테스트 케이스 5~10개

### System Split

이 PRD에서 시스템은 크게 `앱 코드`, `Claude 1P API`, `Claude Code SDK`, `rule engine`으로 나뉜다.

#### 앱 코드

앱 코드는 사용자가 직접 만지는 서비스 로직이다.

- 정책 생성, 수정, 삭제
- policy versioning
- audit log 저장
- diff 생성
- evaluation 실행 버튼
- deployment / rollback 버튼
- 결과 화면 렌더링

즉, 데이터 저장과 화면 흐름, 배포 흐름을 책임진다.

#### Claude 1P API

Claude 1P API는 사용자가 입력한 자연어 정책과 테스트 입력을 해석하는 제품용 모델 API다.

- 자연어 정책을 JSON rule 초안으로 변환
- 테스트 입력을 `prompt injection`, `sensitive data`, `unsafe action` 같은 범주로 분류
- 차단 사유를 사람이 읽을 수 있는 설명으로 생성
- 정책에 맞는 테스트 시나리오를 몇 개 제안

즉, 사용자가 보는 해석층이다.

#### Claude Code SDK

Claude Code SDK는 제품 내부에서 동작하는 자동화 에이전트 계층이다.

- 정책 변경 후 자동 검증 실행
- 실패 로그 요약
- audit log 정리
- `save_policy`, `run_evaluation`, `deploy_policy`, `rollback_policy` 같은 내부 작업 수행

즉, 백오피스 자동화와 운영 오케스트레이션을 맡는다.

#### Rule Engine

rule engine은 실제로 `이 입력을 막을지 말지`를 자동으로 판단하는 부분이다.

- 자연어가 아니라 이미 구조화된 rule JSON을 입력으로 받는다.
- 조건이 맞으면 `blocked`, `masked`, `approval required`, `passed` 중 하나를 반환한다.
- Claude 1P API가 만든 설명이나 추천과 무관하게 최종 판정은 여기서 난다.
- 사람은 기본적으로 이 판정을 직접 하지 않고, `human approval required`가 걸린 경우에만 개입한다.

즉, rule engine은 정책을 실제로 적용하는 자동 판정기다.
정책 수가 늘어나도 rule engine 코드가 정책마다 1:1로 늘어나는 구조가 아니라, 공통 템플릿과 조건 해석 로직을 재사용하는 data-driven 구조로 설계한다.

### Tool Role Split

이 해커톤에서는 아래처럼 역할을 나눈다.

- `Claude 1P API`: 정책 해석, 분류, 설명 생성
- `Claude Code SDK`: 평가 자동화, 운영 오케스트레이션, 로그 요약
- `Claude Code`: 개발할 때 코드 생성, 디버깅, 파일 수정 보조
- `앱 코드`: policy versioning, audit log, diff, evaluation orchestration, deployment, rollback, 화면 렌더링
- `rule engine`: 최종 차단/허용 판단과 정책별 enforcement 결과 계산

### Rule Translation Strategy

처음에는 단순 규칙 매핑으로 시작한다.

- `무시해줘`, `숨겨진 지시문`, `문서 안의 지시문` -> prompt injection block
- `마스킹`, `비밀번호`, `키`, `주민번호` -> sensitive data mask
- `승인`, `허가`, `사람 확인` -> human approval required

이 방식이면 해커톤 시간 안에 충분히 동작하는 데모를 만들 수 있다.

정책 운영 관점에서는 `versioning`, `audit log`, `diff`, `rollback`이 있어야 제품성이 선명해진다.
rule engine은 정책별 분기문을 늘리는 방식이 아니라, `block`, `mask`, `approval` 같은 공통 action과 `contains`, `regex`, `category`, `threshold` 같은 조건 템플릿을 해석하는 방식으로 구현한다.

## 12. Demo Scenario

각 단계 옆에 어떤 컴포넌트가 실제로 동작하는지 명시한다.

1. 사용자가 자연어로 정책을 입력한다.
   └ `Claude 1P API` → 자연어를 Rule JSON 초안으로 변환

2. 시스템이 변환된 rule 목록을 화면에 보여준다.
   └ `앱 코드` → rule 저장, Policy v1 생성, audit log 기록

3. 사용자가 공격 시나리오를 입력한다.
   └ `Rule Engine` → 판정 (block / mask / approval / pass)
   └ `Claude 1P API` → 차단 사유를 한 줄 설명으로 생성

4. 시스템이 차단 결과와 발동 rule을 화면에 보여준다.
   └ `앱 코드` → 결과 렌더링

5. 사용자가 정책 문구를 수정한다.
   └ `Claude 1P API` → 수정된 자연어를 다시 Rule JSON으로 변환
   └ `앱 코드` → Policy v2 생성, diff 계산, audit log 기록
   └ `Claude Code SDK` → 변경 후 자동 검증 실행, 실패 로그 요약

6. 다시 실행해서 결과가 달라지는 것을 보여준다.
   └ `Rule Engine` → v2 기준으로 재판정
   └ `앱 코드` → v1 / v2 결과 나란히 비교 표시

7. 사용자가 v2 정책을 배포하거나 v1으로 롤백한다.
   └ `앱 코드` → status 전환, audit log에 배포/롤백 기록

## 13. Success Metrics

- API 응답 중 로딩 상태가 명확히 표시되고, 사용자가 기다리는 이유를 알 수 있다.
- 테스트 입력에 대한 차단 여부와 발동 rule이 명확히 보인다.
- 정책 수정 전후 diff를 한 화면에서 비교할 수 있다.
- 심사위원이 실제 운영 가능성을 떠올릴 수 있다.

## 14. Risks

- 자연어를 정확한 rule로 바꾸지 못할 수 있다.
- 범위가 커지면 데모가 산만해질 수 있다.
- 내부 구현은 단순해도 제품처럼 보이도록 설명해야 한다.

이 리스크를 줄이기 위해서는 `작게 시작하고, 설명 가능성에 집중`하는 것이 중요하다.

## 15. Future Enhancement

MVP가 완성된 뒤 시간이 남으면, 정책 버전별 `attack pass rate`를 계산하는 기능을 추가한다.

- 특정 정책 버전이 공격 시나리오를 얼마나 통과했는지 측정
- 정책 수정 전후의 방어 성능 비교
- 버전별 성공/실패 케이스 집계
- 가장 자주 뚫리는 공격 유형 시각화

이 기능은 제품의 설득력을 크게 높이지만, 해커톤 MVP의 핵심 범위는 아니다.

## 16. Recommended Positioning

이 제품은 `AI Safety & Security` 트랙에 가장 자연스럽다.

발표 문구는 다음처럼 잡으면 된다.

- 사용자가 자연어로 guardrail 정책을 정의한다.
- 시스템은 이를 구조화된 rule로 변환하고 버전과 audit log를 남긴다.
- 공격 시나리오를 돌려 실제 차단 여부를 검증한다.
- 검증 후 정책을 배포하거나 롤백할 수 있다.
