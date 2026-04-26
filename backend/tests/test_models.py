import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Rule, Policy, AuditEntry, TestResult, ReviseRequest


def test_rule_flat_condition():
    r = Rule(
        id="r1", policy_id="p1",
        action="block",
        condition_type="category",
        condition_value="prompt_injection",
        description="차단",
    )
    assert r.condition_type == "category"
    assert r.condition_value == "prompt_injection"
    assert not hasattr(r, "condition")


def test_policy_has_group_id():
    p = Policy(
        id="policy-001-v1",
        policy_group_id="policy-001",
        name="test",
        natural_language="마스킹해줘",
        status="draft",
        version=1,
        created_at="2026-04-26T00:00:00Z",
    )
    assert p.policy_group_id == "policy-001"
    assert p.version == 1


def test_audit_entry_uses_group_id():
    a = AuditEntry(
        policy_group_id="policy-001",
        policy_name="test",
        version_from=1,
        version_to=2,
        changed_by="operator",
        change_reason="수정",
        timestamp="2026-04-26T00:00:00Z",
    )
    assert a.policy_group_id == "policy-001"
    assert not hasattr(a, "policy_id")


def test_test_result_has_translation_source():
    t = TestResult(
        input_text="test",
        matched_rules=[],
        action="passed",
        reason="없음",
        explanation="통과",
        translation_source="code",
    )
    assert t.translation_source == "code"


def test_revise_request_exists():
    r = ReviseRequest(natural_language="마스킹해줘", change_reason="수정")
    assert r.natural_language == "마스킹해줘"
