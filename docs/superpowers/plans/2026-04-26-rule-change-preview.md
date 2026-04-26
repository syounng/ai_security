# Rule Change Preview (수정 전 Gemini 추천 확인) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 정책 수정 시 Gemini가 생성할 룰 변경안을 저장 전에 미리 보여주고, 사용자가 "적용" 또는 "취소"를 선택하도록 한다.

**Architecture:** 새 `/preview` 엔드포인트가 Gemini 번역 + diff 계산을 수행하되 DB를 변경하지 않는다. 프론트엔드는 "업데이트" 클릭 시 preview를 먼저 호출하고, 변경 내용을 모달로 표시한 뒤 사용자 확인 후에만 실제 PUT을 호출한다.

**Tech Stack:** Python/FastAPI (backend), React/TypeScript/Tailwind (frontend), pytest (tests)

---

## File Map

| 파일 | 작업 |
|------|------|
| `backend/models.py` | `PreviewPolicyRequest` 모델 추가 |
| `backend/main.py` | `POST /policies/{policy_id}/preview` 엔드포인트 추가 |
| `backend/tests/test_preview.py` | 신규 — preview 엔드포인트 단위 테스트 |
| `frontend/lib/api.ts` | `previewPolicy()` 함수 추가 |
| `frontend/components/RuleChangePreviewModal.tsx` | 신규 — diff 표시 + 확인/취소 모달 |
| `frontend/components/PolicyEditor.tsx` | submit 흐름을 preview → 모달 → 확인 시 update로 변경 |

---

## Task 1: Backend — PreviewPolicyRequest 모델

**Files:**
- Modify: `backend/models.py`

- [ ] **Step 1: `PreviewPolicyRequest` 모델 추가**

`backend/models.py` 맨 끝에 추가:

```python
class PreviewPolicyRequest(BaseModel):
    natural_language: str
```

- [ ] **Step 2: 확인**

```bash
cd /Users/soyoung/git/hackerton/backend
python -c "from models import PreviewPolicyRequest; print('OK')"
```

Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add backend/models.py
git commit -m "feat: add PreviewPolicyRequest model"
```

---

## Task 2: Backend — /preview 엔드포인트

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 실패 테스트 작성**

`backend/tests/test_preview.py` 신규 생성:

```python
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import json
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

FAKE_POLICY_ID = "policy-test01"
FAKE_RULE = {
    "id": "rule-aaa",
    "policy_id": FAKE_POLICY_ID,
    "action": "block",
    "condition": {"type": "category", "value": "prompt_injection"},
    "description": "기존 룰",
}
FAKE_POLICY = {
    "id": FAKE_POLICY_ID,
    "name": "테스트 정책",
    "natural_language": "인젝션 차단",
    "policy_type": "content_safety",
    "rule_ids": ["rule-aaa"],
    "status": "draft",
    "version": 1,
    "created_at": "2026-01-01T00:00:00+00:00",
    "updated_at": "2026-01-01T00:00:00+00:00",
}


def test_preview_returns_proposed_rules_and_diff():
    new_rule_data = {"action": "mask", "condition": {"type": "category", "value": "sensitive_data"}, "description": "새 룰"}
    with patch("main.storage.get_policy") as mock_get_policy, \
         patch("main.storage.get_rules_for_policy") as mock_get_rules, \
         patch("main.llm_client.translate_natural_language") as mock_translate:

        from models import Policy, Rule, RuleCondition
        mock_get_policy.return_value = Policy(**FAKE_POLICY)
        mock_get_rules.return_value = [Rule(**FAKE_RULE)]
        mock_translate.return_value = {"success": True, "rules": [new_rule_data]}

        resp = client.post(f"/policies/{FAKE_POLICY_ID}/preview", json={"natural_language": "민감정보 마스킹"})

    assert resp.status_code == 200
    body = resp.json()
    assert "proposed_rules" in body
    assert "diff" in body
    assert "added" in body["diff"]
    assert "removed" in body["diff"]
    assert "unchanged" in body["diff"]


def test_preview_does_not_mutate_storage():
    with patch("main.storage.get_policy") as mock_get_policy, \
         patch("main.storage.get_rules_for_policy") as mock_get_rules, \
         patch("main.storage.update_policy") as mock_update, \
         patch("main.llm_client.translate_natural_language") as mock_translate:

        from models import Policy, Rule
        mock_get_policy.return_value = Policy(**FAKE_POLICY)
        mock_get_rules.return_value = [Rule(**FAKE_RULE)]
        mock_translate.return_value = {"success": True, "rules": [
            {"action": "block", "condition": {"type": "category", "value": "prompt_injection"}, "description": "테스트"}
        ]}

        client.post(f"/policies/{FAKE_POLICY_ID}/preview", json={"natural_language": "인젝션 차단"})

    mock_update.assert_not_called()


def test_preview_returns_404_for_unknown_policy():
    with patch("main.storage.get_policy", return_value=None):
        resp = client.post("/policies/nonexistent/preview", json={"natural_language": "test"})
    assert resp.status_code == 404


def test_preview_returns_422_on_translation_failure():
    with patch("main.storage.get_policy") as mock_get_policy, \
         patch("main.storage.get_rules_for_policy") as mock_get_rules, \
         patch("main.llm_client.translate_natural_language") as mock_translate, \
         patch("main.llm_client.suggest_rephrasing", return_value="다시 써보세요"):

        from models import Policy, Rule
        mock_get_policy.return_value = Policy(**FAKE_POLICY)
        mock_get_rules.return_value = []
        mock_translate.return_value = {"success": False, "error": "parse error", "rules": []}

        resp = client.post(f"/policies/{FAKE_POLICY_ID}/preview", json={"natural_language": "????"})

    assert resp.status_code == 422
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd /Users/soyoung/git/hackerton/backend
python -m pytest tests/test_preview.py -v 2>&1 | head -30
```

Expected: `FAILED` (엔드포인트 없음)

- [ ] **Step 3: preview 엔드포인트 구현**

`backend/main.py`에서 `from models import ...` 줄에 `PreviewPolicyRequest` 추가:

```python
from models import CreatePolicyRequest, UpdatePolicyRequest, EvaluateRequest, TestResult, PreviewPolicyRequest
```

그리고 `get_rules` 함수 아래에 추가:

```python
@app.post("/policies/{policy_id}/preview")
def preview_policy(policy_id: str, req: PreviewPolicyRequest):
    policy = storage.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    old_rules = storage.get_rules_for_policy(policy_id)

    translation = llm_client.translate_natural_language(req.natural_language, policy.policy_type)
    if not translation["success"]:
        suggestion = llm_client.suggest_rephrasing(req.natural_language)
        raise HTTPException(422, detail={"error": "번역 실패", "suggestion": suggestion})

    proposed_rules = [
        {
            "id": f"rule-preview-{i}",
            "policy_id": policy_id,
            "action": r["action"],
            "condition": r["condition"],
            "description": r.get("description", ""),
        }
        for i, r in enumerate(translation["rules"])
    ]

    from models import Rule, RuleCondition
    proposed_rule_objs = [Rule(**r) for r in proposed_rules]
    diff = diff_util.compute_diff(old_rules, proposed_rule_objs)

    return {
        "proposed_rules": proposed_rules,
        "diff": diff,
    }
```

- [ ] **Step 4: 테스트 통과 확인**

```bash
cd /Users/soyoung/git/hackerton/backend
python -m pytest tests/test_preview.py -v
```

Expected: 4 tests PASSED

- [ ] **Step 5: Commit**

```bash
git add backend/main.py backend/models.py backend/tests/test_preview.py
git commit -m "feat: add POST /policies/{id}/preview endpoint (no storage mutation)"
```

---

## Task 3: Frontend — api.ts에 previewPolicy 추가

**Files:**
- Modify: `frontend/lib/api.ts`

- [ ] **Step 1: `PreviewResult` 타입 및 `previewPolicy` 추가**

`frontend/lib/api.ts`에서 `Diff` 타입 선언 바로 아래에 추가:

```typescript
export type PreviewResult = { proposed_rules: Rule[]; diff: Diff };
```

그리고 `api` 객체 안에 `updatePolicy` 바로 아래에 추가:

```typescript
  previewPolicy: (id: string, natural_language: string) =>
    req<PreviewResult>(`/policies/${id}/preview`, {
      method: "POST",
      body: JSON.stringify({ natural_language }),
    }),
```

- [ ] **Step 2: 타입 확인**

```bash
cd /Users/soyoung/git/hackerton/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: 오류 없음

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/api.ts
git commit -m "feat: add previewPolicy API client function"
```

---

## Task 4: RuleChangePreviewModal 컴포넌트

**Files:**
- Create: `frontend/components/RuleChangePreviewModal.tsx`

- [ ] **Step 1: 컴포넌트 작성**

```tsx
"use client";
import { Diff, Rule } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  block: "🚫 차단",
  mask: "🔒 마스킹",
  approval: "👤 승인 필요",
  pass: "✅ 통과",
};

function RuleRow({ rule, highlight }: { rule: Rule; highlight: "added" | "removed" | "unchanged" }) {
  const bg = highlight === "added"
    ? "bg-green-900/30 border-green-700"
    : highlight === "removed"
    ? "bg-red-900/30 border-red-700 line-through opacity-60"
    : "bg-gray-800 border-gray-700";

  const badge = highlight === "added"
    ? <span className="text-green-400 text-xs font-bold mr-2">+ 추가</span>
    : highlight === "removed"
    ? <span className="text-red-400 text-xs font-bold mr-2">- 삭제</span>
    : <span className="text-gray-500 text-xs font-bold mr-2">= 유지</span>;

  return (
    <div className={`rounded p-3 text-sm border ${bg}`}>
      <div className="flex items-center gap-2 flex-wrap">
        {badge}
        <span className="font-mono text-indigo-300 font-semibold">{ACTION_LABELS[rule.action] ?? rule.action}</span>
        <span className="text-gray-600">|</span>
        <span className="text-gray-300 font-mono text-xs">{rule.condition.type}:{rule.condition.value}</span>
      </div>
      {rule.description && <p className="text-gray-400 mt-1 text-xs">{rule.description}</p>}
    </div>
  );
}

type Props = {
  diff: Diff;
  proposedRules: Rule[];
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
};

export default function RuleChangePreviewModal({ diff, proposedRules, onConfirm, onCancel, loading }: Props) {
  const hasChanges = diff.added.length > 0 || diff.removed.length > 0;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-base font-semibold text-gray-100">Gemini 룰 변경 추천</h3>
          <p className="text-xs text-gray-400 mt-1">
            {hasChanges
              ? `${diff.added.length}개 추가 · ${diff.removed.length}개 삭제 · ${diff.unchanged.length}개 유지`
              : "변경 사항이 없습니다."}
          </p>
        </div>

        <div className="overflow-y-auto flex-1 p-4 space-y-2">
          {diff.removed.map((rule, i) => <RuleRow key={`rm-${i}`} rule={rule as Rule} highlight="removed" />)}
          {diff.added.map((rule, i) => <RuleRow key={`add-${i}`} rule={rule as Rule} highlight="added" />)}
          {diff.unchanged.map((rule, i) => <RuleRow key={`unch-${i}`} rule={rule as Rule} highlight="unchanged" />)}
        </div>

        <div className="p-4 border-t border-gray-700 flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-gray-100 rounded px-4 py-2 text-sm font-medium transition-colors"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? "적용 중..." : "이대로 적용"}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: 타입 확인**

```bash
cd /Users/soyoung/git/hackerton/frontend
npx tsc --noEmit 2>&1 | head -20
```

Expected: 오류 없음

- [ ] **Step 3: Commit**

```bash
git add frontend/components/RuleChangePreviewModal.tsx
git commit -m "feat: add RuleChangePreviewModal component"
```

---

## Task 5: PolicyEditor — preview 흐름으로 변경

**Files:**
- Modify: `frontend/components/PolicyEditor.tsx`

- [ ] **Step 1: import 추가**

파일 상단 import 줄 수정:

```typescript
import { api, Policy, Rule, Diff, PolicyType, PreviewResult } from "@/lib/api";
import RuleChangePreviewModal from "./RuleChangePreviewModal";
```

- [ ] **Step 2: 상태 추가**

`const [suggestion, setSuggestion] = useState<string | null>(null);` 아래에 추가:

```typescript
const [preview, setPreview] = useState<PreviewResult | null>(null);
const [pendingNaturalLanguage, setPendingNaturalLanguage] = useState<string>("");
const [applyLoading, setApplyLoading] = useState(false);
```

- [ ] **Step 3: handleSubmit 수정**

기존 `handleSubmit` 함수 전체를 다음으로 교체:

```typescript
const handleSubmit = async () => {
  if (!naturalLanguage.trim()) return;
  setLoading(true);
  setError(null);
  setSuggestion(null);
  try {
    if (isEditing) {
      const res = await api.previewPolicy(selectedPolicy.id, naturalLanguage);
      setPendingNaturalLanguage(naturalLanguage);
      setPreview(res);
    } else {
      if (!name.trim()) { setError("정책 이름을 입력하세요."); setLoading(false); return; }
      const res = await api.createPolicy(name, naturalLanguage, changeReason || "최초 생성", policyType);
      setRules(res.rules);
      onCreated(res.policy, res.rules);
    }
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    try {
      const parsed = JSON.parse(msg);
      if (parsed.suggestion) setSuggestion(parsed.suggestion);
      setError(parsed.error || msg);
    } catch {
      setError(msg);
    }
  } finally {
    setLoading(false);
  }
};
```

- [ ] **Step 4: handleConfirmPreview 핸들러 추가**

`handleSubmit` 함수 바로 아래에 추가:

```typescript
const handleConfirmPreview = async () => {
  if (!selectedPolicy || !preview) return;
  setApplyLoading(true);
  try {
    const res = await api.updatePolicy(selectedPolicy.id, pendingNaturalLanguage, changeReason || "정책 수정");
    setRules(res.rules);
    setPreview(null);
    onUpdated(res.policy, res.rules, res.diff);
  } catch (e: unknown) {
    const msg = e instanceof Error ? e.message : String(e);
    setError(msg);
    setPreview(null);
  } finally {
    setApplyLoading(false);
  }
};
```

- [ ] **Step 5: JSX에 모달 추가**

`return (` 바로 아래 `<div className="space-y-4">` 이전에 추가:

```tsx
{preview && (
  <RuleChangePreviewModal
    diff={preview.diff}
    proposedRules={preview.proposed_rules}
    onConfirm={handleConfirmPreview}
    onCancel={() => setPreview(null)}
    loading={applyLoading}
  />
)}
```

- [ ] **Step 6: 버튼 텍스트 수정**

기존:
```tsx
{loading ? "Gemini로 변환 중..." : isEditing ? "정책 업데이트" : "정책 생성"}
```

변경:
```tsx
{loading ? "Gemini 분석 중..." : isEditing ? "변경 미리보기" : "정책 생성"}
```

- [ ] **Step 7: 타입 확인**

```bash
cd /Users/soyoung/git/hackerton/frontend
npx tsc --noEmit 2>&1 | head -30
```

Expected: 오류 없음

- [ ] **Step 8: 개발 서버에서 동작 확인**

```bash
# 터미널1: 백엔드
cd /Users/soyoung/git/hackerton/backend && uvicorn main:app --reload

# 터미널2: 프론트엔드
cd /Users/soyoung/git/hackerton/frontend && npm run dev
```

확인 항목:
1. 기존 정책 선택 → 자연어 수정 → "변경 미리보기" 클릭
2. 모달이 열리고 추가/삭제/유지 룰이 색상으로 구분되어 표시되는지
3. "이대로 적용" 클릭 시 정책이 실제로 업데이트되는지
4. "취소" 클릭 시 모달만 닫히고 정책은 그대로인지

- [ ] **Step 9: Commit**

```bash
git add frontend/components/PolicyEditor.tsx
git commit -m "feat: show Gemini rule change preview modal before applying policy update"
```
