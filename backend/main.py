from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
import storage
import audit
import rule_engine
import translation
import llm_client
import diff as diff_util
from database import get_db, engine
import orm_models
from models import CreatePolicyRequest, ReviseRequest, EvaluateRequest, TestResult

orm_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Guardrail Control Plane v2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/policies")
def list_policies(db: Session = Depends(get_db)):
    return [p.model_dump() for p in storage.get_all_groups(db)]


@app.get("/policies/{group_id}/versions")
def get_versions(group_id: str, db: Session = Depends(get_db)):
    versions = storage.get_policy_versions(db, group_id)
    if not versions:
        raise HTTPException(404, "Policy group not found")
    return [v.model_dump() for v in versions]


@app.get("/policies/{group_id}/versions/{version}")
def get_version(group_id: str, version: int, db: Session = Depends(get_db)):
    policy_id = f"{group_id}-v{version}"
    policy = storage.get_policy_by_id(db, policy_id)
    if not policy:
        raise HTTPException(404, "Policy version not found")
    rules = storage.get_rules_for_policy(db, policy_id)
    return {"policy": policy.model_dump(), "rules": [r.model_dump() for r in rules]}


@app.post("/policies")
def create_policy(req: CreatePolicyRequest, db: Session = Depends(get_db)):
    result = translation.translate(req.natural_language, req.policy_type)
    if not result["success"]:
        suggestion = llm_client.suggest_rephrasing(req.natural_language)
        raise HTTPException(422, detail={"error": "번역 실패", "suggestion": suggestion})
    policy, rules = storage.create_policy(db, req.name, req.natural_language, result["rules"], req.policy_type)
    audit.record(
        policy_group_id=policy.policy_group_id,
        policy_name=policy.name,
        version_from=None,
        version_to=policy.version,
        change_reason=req.change_reason,
    )
    return {
        "policy": policy.model_dump(),
        "rules": [r.model_dump() for r in rules],
        "translation_source": result["source"],
    }


@app.post("/policies/{group_id}/revise")
def revise_policy(group_id: str, req: ReviseRequest, db: Session = Depends(get_db)):
    versions = storage.get_policy_versions(db, group_id)
    if not versions:
        raise HTTPException(404, "Policy group not found")
    latest = versions[0]
    old_rules = storage.get_rules_for_policy(db, latest.id)

    result = translation.translate(req.natural_language, latest.policy_type)
    if not result["success"]:
        suggestion = llm_client.suggest_rephrasing(req.natural_language)
        raise HTTPException(422, detail={"error": "번역 실패", "suggestion": suggestion})

    policy, new_rules = storage.revise_policy(db, group_id, req.natural_language, result["rules"])
    diff = diff_util.compute_diff(old_rules, new_rules)

    audit.record(
        policy_group_id=group_id,
        policy_name=policy.name,
        version_from=latest.version,
        version_to=policy.version,
        change_reason=req.change_reason,
    )
    return {
        "policy": policy.model_dump(),
        "rules": [r.model_dump() for r in new_rules],
        "diff": diff,
        "translation_source": result["source"],
    }


@app.get("/policies/{group_id}/diff")
def get_diff(group_id: str, from_v: int, to_v: int, db: Session = Depends(get_db)):
    from_rules = storage.get_rules_for_policy(db, f"{group_id}-v{from_v}")
    to_rules = storage.get_rules_for_policy(db, f"{group_id}-v{to_v}")
    if not from_rules and not to_rules:
        raise HTTPException(404, "Version not found")
    return diff_util.compute_diff(from_rules, to_rules)


@app.post("/policies/{group_id}/versions/{version}/deploy")
def deploy_policy(group_id: str, version: int, db: Session = Depends(get_db)):
    policy_id = f"{group_id}-v{version}"
    policy = storage.get_policy_by_id(db, policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    updated = storage.deploy_policy(db, policy_id)
    audit.record(
        policy_group_id=group_id, policy_name=updated.name,
        version_from=policy.version, version_to=policy.version,
        change_reason="배포 (active 전환)",
    )
    return updated.model_dump()


@app.post("/policies/{group_id}/rollback")
def rollback_policy(group_id: str, db: Session = Depends(get_db)):
    versions = storage.get_policy_versions(db, group_id)
    if len(versions) < 2:
        raise HTTPException(400, "롤백할 이전 버전이 없습니다")
    updated = storage.rollback_policy(db, group_id)
    audit.record(
        policy_group_id=group_id, policy_name=updated.name,
        version_from=versions[0].version, version_to=updated.version,
        change_reason="롤백",
    )
    return updated.model_dump()


@app.post("/evaluate")
def evaluate(req: EvaluateRequest, db: Session = Depends(get_db)):
    policy = storage.get_policy_by_id(db, req.policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    rules = storage.get_rules_for_policy(db, req.policy_id)

    result = rule_engine.evaluate(req.input_text, rules)
    matched_objs = [r for r in rules if r.id in result["matched_rules"]]
    matched_descs = [r.description for r in matched_objs]

    # 룰에 아무것도 안 걸린 경우 Gemini 2차 안전 판정 — policy_type별 전문 프롬프트 사용
    if result["action"] == "passed" and not result["matched_rules"]:
        judge = llm_client.safety_judge_for_category(req.input_text, policy.policy_type)
        return TestResult(
            input_text=req.input_text,
            matched_rules=[],
            action=judge["action"],
            reason=judge["reason"],
            explanation=judge["reason"],
            translation_source="gemini",
            gemini_error=judge.get("gemini_error", False),
        ).model_dump()

    explanation = llm_client.generate_explanation(
        input_text=req.input_text,
        action=result["action"],
        matched_rules=matched_descs,
        matched_text=result.get("matched_text"),
    )
    return TestResult(
        input_text=req.input_text,
        matched_rules=result["matched_rules"],
        action=result["action"],
        reason=matched_descs[0] if matched_descs else "매칭된 규칙 없음",
        explanation=explanation,
        translation_source="rule_engine",
    ).model_dump()


@app.get("/audit-logs")
def get_audit_logs():
    return [e.model_dump() for e in audit.get_all()]


@app.get("/audit-logs/{group_id}")
def get_audit_logs_for_group(group_id: str):
    return [e.model_dump() for e in audit.get_by_group(group_id)]
