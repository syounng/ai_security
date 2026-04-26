# Tech Stack Design: Natural Language Guardrail Control Plane

Date: 2026-04-26

## Overview

1일 해커톤용 Natural Language Guardrail Control Plane의 기술 스택 설계.
사용자가 자연어로 AI 안전 정책을 입력하면 구조화된 rule로 변환하고, 버전 관리 · 검증 · 배포 · 롤백까지 운영 흐름을 보여주는 제품.

## Decisions

| 항목 | 선택 | 이유 |
|------|------|------|
| AI API | Gemini API (gemini-2.0-flash) | .env 키 보유, 구조화 출력 지원 |
| 프론트 프레임워크 | Next.js 15 (App Router) | Vercel 배포 최적화, React 기반 |
| UI 컴포넌트 | shadcn/ui + Tailwind CSS | 빠른 프로토타입, 완성도 높은 UI |
| 백엔드 프레임워크 | FastAPI (Python 3.12) | Gemini Python SDK, rule engine 통합 편의 |
| ORM | SQLAlchemy + Alembic | SQLite 연동, 마이그레이션 지원 |
| 저장소 | SQLite | 별도 DB 서버 불필요, versioning/audit log SQL 처리 |
| 상태 관리 | TanStack Query (React Query) | API 캐싱, 낙관적 업데이트 |
| 프론트 배포 | Vercel | 무료 티어, 자동 CI/CD |
| 백엔드 배포 | Railway | SQLite persistent volume, 무료 티어 |

## Architecture

```
[Browser]
    │
    ▼
[Next.js 15 — Vercel]
  App Router
  shadcn/ui + Tailwind
  TanStack Query
    │  REST API
    ▼
[FastAPI — Railway]
  /policies      CRUD + versioning
  /rules         rule 조회
  /evaluate      test harness 실행
  /audit-logs    audit log 조회
  /deploy        배포 / 롤백
    │
    ├──▶ [Rule Engine] (순수 Python)
    │      contains / regex / category / threshold 조건 해석
    │      block / mask / approval / pass 판정
    │
    ├──▶ [Gemini API]
    │      자연어 → Rule JSON 변환 (response_schema 구조화 출력)
    │      차단 사유 설명 생성
    │      테스트 시나리오 제안
    │
    └──▶ [SQLite]
           policies   (id, name, natural_language, status, version, ...)
           rules      (id, policy_id, action, condition_type, condition_value, ...)
           audit_logs (policy_id, version_from, version_to, changed_by, reason, timestamp)
```

## Component Responsibilities

### Frontend (Next.js)

- `PolicyEditor` — 자연어 입력 textarea, 변환 트리거 버튼
- `RulePreview` — 변환된 rule 목록, 각 rule 설명
- `TestHarness` — 테스트 입력 폼, 결과(block/mask/approval/pass) 표시, 발동 rule 강조
- `DiffViewer` — 정책 버전 전후 diff (shadcn/ui Table + badge)
- `AuditLog` — 변경 이력 테이블, 변경 사유
- `DeployPanel` — 배포 버튼, 롤백 버튼, 현재 active 버전 표시

### Backend (FastAPI)

- `policy_router` — 정책 CRUD, 버전 bump, diff 계산
- `evaluate_router` — rule engine 호출, Gemini 설명 생성, 결과 반환
- `deploy_router` — status 전환(draft → active), rollback
- `audit_router` — audit log 조회

### Rule Engine (Python)

data-driven 구조. 정책마다 코드가 늘지 않고 조건 템플릿을 해석하는 방식.

```python
conditions = {
  "contains":   lambda text, val: val.lower() in text.lower(),
  "regex":      lambda text, val: bool(re.search(val, text)),
  "category":   lambda text, val: classifier.predict(text) == val,
  "threshold":  lambda text, val: classifier.score(text) >= float(val),
}
```

### Gemini API 사용처

| 용도 | 모델 | 출력 |
|------|------|------|
| 자연어 → Rule JSON | gemini-2.0-flash | `response_schema` 구조화 출력 |
| 차단 사유 설명 | gemini-2.0-flash | 자유 텍스트 (1~2문장) |
| 테스트 시나리오 제안 | gemini-2.0-flash | 자유 텍스트 리스트 |

## Data Model

```sql
-- 정책 (여러 버전 보존)
policies (
  id TEXT PRIMARY KEY,
  name TEXT,
  natural_language TEXT,
  status TEXT,          -- draft | active | archived
  version INTEGER,
  created_at DATETIME,
  updated_at DATETIME
)

-- rule (policy_id로 특정 버전 정책에 귀속)
rules (
  id TEXT PRIMARY KEY,
  policy_id TEXT,
  action TEXT,          -- block | mask | approval | pass
  condition_type TEXT,  -- contains | regex | category | threshold
  condition_value TEXT,
  description TEXT
)

-- 감사 로그
audit_logs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  policy_id TEXT,
  version_from INTEGER,
  version_to INTEGER,
  changed_by TEXT,      -- MVP: 고정값 "operator"
  change_reason TEXT,
  timestamp DATETIME
)
```

## API Endpoints

| Method | Path | 설명 |
|--------|------|------|
| POST | /policies | 자연어 → rule 변환 + 정책 저장 (v1) |
| GET | /policies | 정책 목록 |
| GET | /policies/{id} | 정책 상세 + rule 목록 |
| PUT | /policies/{id} | 정책 수정 → 버전 bump + audit log |
| GET | /policies/{id}/diff | 버전 전후 diff |
| POST | /policies/{id}/evaluate | 테스트 입력 실행 |
| POST | /policies/{id}/deploy | active 배포 |
| POST | /policies/{id}/rollback | 이전 버전으로 롤백 |
| GET | /audit-logs/{policy_id} | audit log 조회 |

## Non-Functional Constraints

- 1일 해커톤 구현 범위
- 데모 흐름은 1분 이내 이해 가능
- Gemini API 응답 중 로딩 표시 필수 (UX)
- SQLite는 Railway persistent volume에 마운트
- 인증 없음 (MVP 범위 외)

## Out of Scope

- 실제 production-grade 보안
- 멀티테넌시
- 모델 재학습
- 실제 외부 API 연동
