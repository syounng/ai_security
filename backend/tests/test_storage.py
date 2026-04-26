import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base
import storage

@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

_RULES = [{"action": "mask", "condition_type": "category", "condition_value": "sensitive_data", "description": "마스킹"}]

def test_create_policy_generates_group_id(db):
    policy, rules = storage.create_policy(db, "테스트", "마스킹해줘", _RULES)
    assert policy.policy_group_id.startswith("policy-")
    assert policy.id == f"{policy.policy_group_id}-v1"
    assert policy.version == 1
    assert policy.status == "draft"
    assert len(rules) == 1

def test_revise_creates_new_row(db):
    policy, _ = storage.create_policy(db, "테스트", "마스킹해줘", _RULES)
    gid = policy.policy_group_id
    new_rules = [{"action": "block", "condition_type": "category", "condition_value": "prompt_injection", "description": "차단"}]
    v2, _ = storage.revise_policy(db, gid, "차단해줘", new_rules)
    assert v2.version == 2
    assert v2.id == f"{gid}-v2"
    versions = storage.get_policy_versions(db, gid)
    assert len(versions) == 2

def test_rollback_flips_status(db):
    policy, _ = storage.create_policy(db, "테스트", "마스킹해줘", _RULES)
    gid = policy.policy_group_id
    storage.deploy_policy(db, policy.id)
    new_rules = [{"action": "block", "condition_type": "category", "condition_value": "prompt_injection", "description": "차단"}]
    v2, _ = storage.revise_policy(db, gid, "차단해줘", new_rules)
    storage.deploy_policy(db, v2.id)
    rolled = storage.rollback_policy(db, gid)
    assert rolled.version == 1
    assert rolled.status == "active"
    v2_check = storage.get_policy_by_id(db, v2.id)
    assert v2_check.status == "archived"

def test_get_all_groups_returns_latest(db):
    policy, _ = storage.create_policy(db, "테스트", "마스킹해줘", _RULES)
    gid = policy.policy_group_id
    new_rules = [{"action": "block", "condition_type": "category", "condition_value": "prompt_injection", "description": "차단"}]
    storage.revise_policy(db, gid, "차단해줘", new_rules)
    groups = storage.get_all_groups(db)
    assert len(groups) == 1
    assert groups[0].version == 2
