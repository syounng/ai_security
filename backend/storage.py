import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple, List
from models import Policy, Rule

DATA_DIR = Path(__file__).parent.parent / "data"
POLICIES_FILE = DATA_DIR / "policies.json"


def _load() -> dict:
    return json.loads(POLICIES_FILE.read_text(encoding="utf-8"))


def _save(data: dict) -> None:
    POLICIES_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def get_all_policies() -> list[Policy]:
    data = _load()
    return [Policy(**p) for p in data["policies"]]


def get_policy(policy_id: str) -> Optional[Policy]:
    data = _load()
    for p in data["policies"]:
        if p["id"] == policy_id:
            return Policy(**p)
    return None


def get_rules_for_policy(policy_id: str) -> list[Rule]:
    data = _load()
    return [Rule(**r) for r in data["rules"] if r["policy_id"] == policy_id]


def get_rule(rule_id: str) -> Optional[Rule]:
    data = _load()
    for r in data["rules"]:
        if r["id"] == rule_id:
            return Rule(**r)
    return None


def create_policy(name: str, natural_language: str, rules_data: List[dict]) -> Tuple[Policy, List[Rule]]:
    data = _load()
    now = datetime.now(timezone.utc).isoformat()
    policy_id = f"policy-{uuid.uuid4().hex[:8]}"

    rules = []
    rule_ids = []
    for rd in rules_data:
        rule_id = f"rule-{uuid.uuid4().hex[:8]}"
        rule = Rule(
            id=rule_id,
            policy_id=policy_id,
            action=rd["action"],
            condition=rd["condition"],
            description=rd.get("description", ""),
        )
        rules.append(rule)
        rule_ids.append(rule_id)

    policy = Policy(
        id=policy_id,
        name=name,
        natural_language=natural_language,
        rule_ids=rule_ids,
        status="draft",
        version=1,
        created_at=now,
        updated_at=now,
    )

    data["policies"].append(policy.model_dump())
    data["rules"].extend([r.model_dump() for r in rules])
    _save(data)
    return policy, rules


def update_policy(policy_id: str, natural_language: str, rules_data: List[dict]) -> Tuple[Policy, List[Rule]]:
    data = _load()
    now = datetime.now(timezone.utc).isoformat()

    rules = []
    rule_ids = []
    for rd in rules_data:
        rule_id = f"rule-{uuid.uuid4().hex[:8]}"
        rule = Rule(
            id=rule_id,
            policy_id=policy_id,
            action=rd["action"],
            condition=rd["condition"],
            description=rd.get("description", ""),
        )
        rules.append(rule)
        rule_ids.append(rule_id)

    for p in data["policies"]:
        if p["id"] == policy_id:
            p["previous_rule_ids"] = p.get("rule_ids", [])
            p["natural_language"] = natural_language
            p["rule_ids"] = rule_ids
            p["version"] += 1
            p["updated_at"] = now

    data["rules"].extend([r.model_dump() for r in rules])
    _save(data)

    policy = get_policy(policy_id)
    return policy, rules


def deploy_policy(policy_id: str) -> Policy:
    data = _load()
    for p in data["policies"]:
        if p["id"] == policy_id:
            p["status"] = "active"
    _save(data)
    return get_policy(policy_id)


def rollback_policy(policy_id: str) -> Policy:
    data = _load()
    for p in data["policies"]:
        if p["id"] == policy_id:
            prev = p.get("previous_rule_ids", [])
            if prev:
                p["rule_ids"], p["previous_rule_ids"] = prev, p["rule_ids"]
                p["version"] = max(1, p["version"] - 1)
                p["updated_at"] = datetime.now(timezone.utc).isoformat()
            p["status"] = "draft"
    _save(data)
    return get_policy(policy_id)
