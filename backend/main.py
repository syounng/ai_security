from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import storage
import audit
import rule_engine
import llm_client
import diff as diff_util
from models import CreatePolicyRequest, UpdatePolicyRequest, EvaluateRequest, TestResult, PreviewPolicyRequest

app = FastAPI(title="Guardrail Control Plane")

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
def list_policies():
    return [p.model_dump() for p in storage.get_all_policies()]


@app.get("/policies/{policy_id}")
def get_policy(policy_id: str):
    policy = storage.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    rules = storage.get_rules_for_policy(policy_id)
    return {"policy": policy.model_dump(), "rules": [r.model_dump() for r in rules]}


@app.post("/policies")
def create_policy(req: CreatePolicyRequest):
    translation = llm_client.translate_natural_language(req.natural_language, req.policy_type)
    if not translation["success"]:
        suggestion = llm_client.suggest_rephrasing(req.natural_language)
        raise HTTPException(422, detail={"error": "번역 실패", "suggestion": suggestion})

    policy, rules = storage.create_policy(req.name, req.natural_language, translation["rules"], req.policy_type)
    audit.record(
        policy_id=policy.id,
        policy_name=policy.name,
        version_from=None,
        version_to=policy.version,
        change_reason=req.change_reason,
    )
    return {"policy": policy.model_dump(), "rules": [r.model_dump() for r in rules]}


@app.put("/policies/{policy_id}")
def update_policy(policy_id: str, req: UpdatePolicyRequest):
    old_policy = storage.get_policy(policy_id)
    if not old_policy:
        raise HTTPException(404, "Policy not found")
    old_rules = storage.get_rules_for_policy(policy_id)

    translation = llm_client.translate_natural_language(req.natural_language, old_policy.policy_type)
    if not translation["success"]:
        suggestion = llm_client.suggest_rephrasing(req.natural_language)
        raise HTTPException(422, detail={"error": "번역 실패", "suggestion": suggestion})

    policy, new_rules = storage.update_policy(policy_id, req.natural_language, translation["rules"])
    diff = diff_util.compute_diff(old_rules, new_rules)

    audit.record(
        policy_id=policy.id,
        policy_name=policy.name,
        version_from=old_policy.version,
        version_to=policy.version,
        change_reason=req.change_reason,
    )
    return {
        "policy": policy.model_dump(),
        "rules": [r.model_dump() for r in new_rules],
        "diff": diff,
    }


@app.post("/policies/{policy_id}/deploy")
def deploy_policy(policy_id: str):
    policy = storage.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    updated = storage.deploy_policy(policy_id)
    audit.record(
        policy_id=policy_id,
        policy_name=policy.name,
        version_from=policy.version,
        version_to=policy.version,
        change_reason="배포 (active 전환)",
    )
    return updated.model_dump()


@app.post("/policies/{policy_id}/rollback")
def rollback_policy(policy_id: str):
    policy = storage.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    updated = storage.rollback_policy(policy_id)
    audit.record(
        policy_id=policy_id,
        policy_name=policy.name,
        version_from=policy.version,
        version_to=policy.version,
        change_reason="롤백 (inactive 전환)",
    )
    return updated.model_dump()


@app.post("/policies/{policy_id}/to-draft")
def to_draft_policy(policy_id: str):
    policy = storage.get_policy(policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    updated = storage.to_draft_policy(policy_id)
    audit.record(
        policy_id=policy_id,
        policy_name=policy.name,
        version_from=policy.version,
        version_to=policy.version,
        change_reason="초안으로 전환 (재검토)",
    )
    return updated.model_dump()


@app.post("/evaluate")
def evaluate(req: EvaluateRequest):
    policy = storage.get_policy(req.policy_id)
    if not policy:
        raise HTTPException(404, "Policy not found")
    rules = storage.get_rules_for_policy(req.policy_id)

    _EVAL_STAGE = {
        "prompt_defense": "input",
        "sensitive_data": "output",
        "content_safety": "both",
        "compliance": "input",
    }
    stage = _EVAL_STAGE.get(policy.policy_type, "input")
    if stage == "output" and req.output_text:
        eval_text = req.output_text
    elif stage == "both" and req.output_text:
        eval_text = req.input_text + "\n\n" + req.output_text
    else:
        eval_text = req.input_text

    result = rule_engine.evaluate(eval_text, rules)
    matched_rule_objs = [storage.get_rule(rid) for rid in result["matched_rules"]]
    matched_descs = [r.description for r in matched_rule_objs if r]

    explanation = llm_client.generate_explanation(
        input_text=eval_text,
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
    ).model_dump()


@app.get("/audit-logs")
def get_audit_logs():
    return [e.model_dump() for e in audit.get_all()]


@app.get("/policies/{policy_id}/rules")
def get_rules(policy_id: str):
    return [r.model_dump() for r in storage.get_rules_for_policy(policy_id)]


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

    from models import Rule
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

    proposed_rule_objs = [Rule(**r) for r in proposed_rules]
    diff = diff_util.compute_diff(old_rules, proposed_rule_objs)

    return {
        "proposed_rules": proposed_rules,
        "diff": diff,
    }
