import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session
from orm_models import PolicyORM, RuleORM
from models import Policy, Rule


def _to_policy(p: PolicyORM) -> Policy:
    return Policy(
        id=p.id,
        policy_group_id=p.policy_group_id,
        name=p.name,
        natural_language=p.natural_language,
        status=p.status,
        version=p.version,
        created_at=p.created_at.isoformat() if p.created_at else "",
    )


def _to_rule(r: RuleORM) -> Rule:
    return Rule(
        id=r.id,
        policy_id=r.policy_id,
        action=r.action,
        condition_type=r.condition_type,
        condition_value=r.condition_value,
        description=r.description,
    )


def _build_rules(db: Session, policy_id: str, rules_data: List[dict]) -> List[RuleORM]:
    orms = []
    for rd in rules_data:
        orm = RuleORM(
            id=f"rule-{uuid.uuid4().hex[:8]}",
            policy_id=policy_id,
            action=rd["action"],
            condition_type=rd["condition_type"],
            condition_value=rd["condition_value"],
            description=rd.get("description", ""),
        )
        db.add(orm)
        orms.append(orm)
    return orms


def get_all_groups(db: Session) -> List[Policy]:
    subq = (
        db.query(PolicyORM.policy_group_id, func.max(PolicyORM.version).label("max_v"))
        .group_by(PolicyORM.policy_group_id)
        .subquery()
    )
    rows = (
        db.query(PolicyORM)
        .join(subq, (PolicyORM.policy_group_id == subq.c.policy_group_id) &
                    (PolicyORM.version == subq.c.max_v))
        .all()
    )
    return [_to_policy(r) for r in rows]


def get_policy_versions(db: Session, group_id: str) -> List[Policy]:
    rows = (
        db.query(PolicyORM)
        .filter(PolicyORM.policy_group_id == group_id)
        .order_by(PolicyORM.version.desc())
        .all()
    )
    return [_to_policy(r) for r in rows]


def get_policy_by_id(db: Session, policy_id: str) -> Optional[Policy]:
    row = db.query(PolicyORM).filter(PolicyORM.id == policy_id).first()
    return _to_policy(row) if row else None


def get_latest_policy(db: Session, group_id: str) -> Optional[Policy]:
    row = (
        db.query(PolicyORM)
        .filter(PolicyORM.policy_group_id == group_id)
        .order_by(PolicyORM.version.desc())
        .first()
    )
    return _to_policy(row) if row else None


def get_rules_for_policy(db: Session, policy_id: str) -> List[Rule]:
    rows = db.query(RuleORM).filter(RuleORM.policy_id == policy_id).all()
    return [_to_rule(r) for r in rows]


def create_policy(db: Session, name: str, natural_language: str, rules_data: List[dict]) -> Tuple[Policy, List[Rule]]:
    now = datetime.now(timezone.utc)
    group_id = f"policy-{uuid.uuid4().hex[:8]}"
    policy_id = f"{group_id}-v1"

    orm = PolicyORM(
        id=policy_id, policy_group_id=group_id, name=name,
        natural_language=natural_language, status="draft", version=1, created_at=now,
    )
    db.add(orm)
    rule_orms = _build_rules(db, policy_id, rules_data)
    db.commit()
    return _to_policy(orm), [_to_rule(r) for r in rule_orms]


def revise_policy(db: Session, group_id: str, natural_language: str, rules_data: List[dict]) -> Tuple[Policy, List[Rule]]:
    latest = get_latest_policy(db, group_id)
    if not latest:
        raise ValueError(f"Policy group {group_id} not found")

    now = datetime.now(timezone.utc)
    new_version = latest.version + 1
    new_id = f"{group_id}-v{new_version}"

    db.query(PolicyORM).filter(
        PolicyORM.policy_group_id == group_id,
        PolicyORM.status == "active",
    ).update({"status": "archived"})

    orm = PolicyORM(
        id=new_id, policy_group_id=group_id, name=latest.name,
        natural_language=natural_language, status="draft",
        version=new_version, created_at=now,
    )
    db.add(orm)
    rule_orms = _build_rules(db, new_id, rules_data)
    db.commit()
    return _to_policy(orm), [_to_rule(r) for r in rule_orms]


def deploy_policy(db: Session, policy_id: str) -> Policy:
    row = db.query(PolicyORM).filter(PolicyORM.id == policy_id).first()
    if not row:
        raise ValueError("Policy not found")
    db.query(PolicyORM).filter(
        PolicyORM.policy_group_id == row.policy_group_id,
        PolicyORM.status == "active",
    ).update({"status": "archived"})
    row.status = "active"
    db.commit()
    return _to_policy(row)


def rollback_policy(db: Session, group_id: str) -> Policy:
    versions = get_policy_versions(db, group_id)
    if len(versions) < 2:
        raise ValueError("롤백할 이전 버전이 없습니다")
    current, previous = versions[0], versions[1]
    db.query(PolicyORM).filter(PolicyORM.id == current.id).update({"status": "archived"})
    db.query(PolicyORM).filter(PolicyORM.id == previous.id).update({"status": "active"})
    db.commit()
    return get_policy_by_id(db, previous.id)
