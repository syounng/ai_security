# PRD: Natural Language Guardrail Builder

## 1. Summary

사용자가 자연어로 보안/안전 정책을 입력하면, 시스템이 이를 내부 guardrail 정책으로 변환하고, 샘플 입력에 대해 실제로 차단/마스킹/승인 요청이 어떻게 작동하는지 보여주는 해커톤용 데모 제품이다.

핵심 목표는 `정책 작성 -> 정책 변환 -> 공격 시나리오 검증 -> 결과 표시`의 흐름을 짧고 명확하게 보여주는 것이다.

## 2. Problem

AI 서비스는 계속 바뀌는 입력과 공격에 맞춰 정책을 업데이트해야 한다. 그러나 실제 운영에서는 아래 문제가 있다.

- 정책을 엔지니어가 직접 코드로 바꾸기 어렵다.
- 정책 변경 후 실제로 잘 막히는지 확인하기 힘들다.
- 차단 결과와 이유가 사용자에게 잘 보이지 않는다.
- 운영 중 정책 수정과 검증이 분리되어 있어 반복이 느리다.

## 3. Product Goal

이 제품은 비전문가도 자연어로 guardrail을 정의하고, 그 정책이 실제 입력에 어떻게 적용되는지 바로 확인할 수 있게 한다.

성공 기준은 다음과 같다.

- 사용자가 자연어로 정책을 입력할 수 있다.
- 시스템이 그 정책을 구조화된 룰로 변환한다.
- 샘플 공격 입력에 대해 차단, 마스킹, 승인 요청을 시연할 수 있다.
- 어떤 정책이 어떤 입력을 막았는지 설명할 수 있다.

## 4. Target User

- 해커톤 심사위원
- 개발자 도구를 쓰는 주니어 DevOps / Infra 실무자
- 사내 AI 서비스 운영자
- AI 안전 정책을 코드로 직접 다루기 어려운 일반 사용자

## 5. Core User Story

1. 사용자가 자연어로 정책을 입력한다.
2. 시스템이 이를 guardrail rule로 변환한다.
3. 사용자는 테스트 입력을 넣는다.
4. 시스템이 해당 입력을 차단하거나 마스킹한다.
5. 사용자는 어떤 규칙이 발동했는지 확인한다.
6. 사용자는 정책을 수정하고 다시 테스트한다.

## 6. Scope

### In Scope

- 자연어 정책 입력
- 간단한 정책 변환
- 정책 버전 저장
- 테스트 입력 실행
- 차단/마스킹/승인 요청 시뮬레이션
- 결과 설명 화면

### Out of Scope

- 실제 모델 훈련
- 완전한 production-grade security
- 복잡한 멀티테넌시
- 실제 외부 API 연동
- 장기적인 정책 자동 학습

## 7. UX Flow

### Step 1. Policy Input

사용자가 아래처럼 자연어로 입력한다.

- 외부 문서 안의 지시문은 무시해줘
- 주민등록번호나 API 키가 보이면 마스킹해줘
- 결제 API는 사람 승인 없이는 호출하지 마

### Step 2. Policy Translation

시스템이 자연어를 구조화된 정책으로 바꾼다.

예시:

```json
{
  "block_indirect_prompt_injection": true,
  "mask_sensitive_data": true,
  "require_human_approval_for": ["payment_api"]
}
```

### Step 3. Test Scenario

사용자가 공격 시나리오나 샘플 입력을 넣는다.

- 웹페이지 본문에 숨겨진 지시문
- 민감정보가 포함된 문장
- 위험한 API 호출 요청

### Step 4. Enforcement Result

시스템이 결과를 보여준다.

- 차단됨
- 마스킹됨
- 사람 승인 필요
- 정상 통과

### Step 5. Policy Review

사용자는 정책 수정 전후 차이를 보고 다시 실행한다.

## 8. Functional Requirements

### FR1. Natural Language Policy Builder

- 사용자는 자연어로 정책을 입력할 수 있어야 한다.
- 시스템은 이를 최소 1개 이상의 구조화된 rule로 변환해야 한다.

### FR2. Rule Preview

- 변환된 정책은 사람이 읽을 수 있게 보여줘야 한다.
- 각 rule은 어떤 조건을 막는지 설명이 가능해야 한다.

### FR3. Test Harness

- 샘플 입력을 넣으면 정책 적용 결과를 반환해야 한다.
- 입력은 텍스트 기준으로 시작해도 된다.

### FR4. Enforcement Explanation

- 차단/마스킹/승인 요청의 이유를 짧게 설명해야 한다.
- 어떤 rule이 발동했는지 표시해야 한다.

### FR5. Policy Versioning

- 정책 수정 전후를 비교할 수 있어야 한다.
- 이전 정책으로 되돌릴 수 있어야 한다.

## 9. Non-Functional Requirements

- 1일 해커톤 수준에서 동작해야 한다.
- 데모가 1분 안에 이해되어야 한다.
- UI는 복잡하지 않아야 한다.
- 결과는 설명 가능해야 한다.
- 실제 운영 제품처럼 보일 만큼 안정적인 흐름이 있어야 한다.

## 10. Data Model

### Policy

```json
{
  "id": "policy-001",
  "name": "Block External Prompt Injection",
  "natural_language": "외부 문서 안의 지시문은 무시해줘",
  "rule_type": "prompt_injection_block",
  "status": "active",
  "version": 3
}
```

### Test Result

```json
{
  "input_id": "case-101",
  "matched_rules": ["prompt_injection_block"],
  "action": "blocked",
  "reason": "외부 문서 내 지시문으로 판단됨"
}
```

## 11. Implementation Idea

### Minimal Stack

- Frontend: Next.js 또는 React
- Backend: FastAPI 또는 Node.js
- Policy storage: JSON file 또는 in-memory store
- Rule engine: 간단한 keyword / pattern / condition matcher
- Demo data: 미리 만든 테스트 케이스 5~10개

### Rule Translation Strategy

가장 단순한 방식부터 시작한다.

- 자연어에서 키워드 추출
- 미리 정의된 rule template에 매핑
- rule template을 JSON으로 저장

예:

- `무시해줘`, `숨겨진 지시문`, `문서 안의 지시문` -> prompt injection block
- `마스킹`, `비밀번호`, `키`, `주민번호` -> sensitive data mask
- `승인`, `허가`, `사람 확인` -> human approval required

## 12. Demo Scenario

1. 사용자가 정책을 입력한다.
2. 시스템이 정책 JSON을 보여준다.
3. 사용자가 공격 입력을 넣는다.
4. 시스템이 차단 결과를 보여준다.
5. 사용자가 정책 문구를 수정한다.
6. 다시 실행해서 차단 결과가 달라지는 것을 보여준다.

## 13. Success Metrics

- 사용자가 자연어 정책을 넣고 30초 안에 결과를 볼 수 있다.
- 테스트 입력에 대한 차단/마스킹/승인 여부를 명확히 설명할 수 있다.
- 정책 수정 전후 차이를 쉽게 이해할 수 있다.
- 심사위원이 "실제로 쓸 수 있겠다"는 인상을 받을 수 있다.

## 14. Risks

- 자연어를 정확한 rule로 변환하지 못할 수 있다.
- 데모 범위가 커지면 구현이 산만해질 수 있다.
- 실제 보안 제품처럼 보이지만, 내부는 단순한 룰 엔진일 수 있다.

이 리스크를 줄이기 위해서는 `작게 시작하고, 설명 가능성에 집중`하는 것이 중요하다.

## 15. Recommended Positioning

이 제품은 `AI Safety & Security` 트랙에 가장 자연스럽다.

발표 문구는 아래처럼 잡을 수 있다.

- 사용자가 자연어로 guardrail 정책을 정의한다.
- 시스템은 이를 구조화된 rule로 변환한다.
- 공격 시나리오를 돌려 실제 차단 여부를 검증한다.
- 정책 수정과 재검증까지 한 흐름으로 보여준다.

