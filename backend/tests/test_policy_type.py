import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Policy, CreatePolicyRequest, EvaluateRequest

def test_policy_has_policy_type_field():
    p = Policy(
        id="p1", name="test", natural_language="test nl",
        policy_type="prompt_defense",
        rule_ids=[], status="draft", version=1,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert p.policy_type == "prompt_defense"

def test_policy_type_defaults_to_content_safety():
    p = Policy(
        id="p1", name="test", natural_language="test nl",
        rule_ids=[], status="draft", version=1,
        created_at="2026-01-01T00:00:00+00:00",
        updated_at="2026-01-01T00:00:00+00:00",
    )
    assert p.policy_type == "content_safety"

def test_create_request_accepts_policy_type():
    req = CreatePolicyRequest(name="x", natural_language="y", policy_type="sensitive_data")
    assert req.policy_type == "sensitive_data"

def test_evaluate_request_accepts_output_text():
    req = EvaluateRequest(policy_id="p1", input_text="hello", output_text="world")
    assert req.output_text == "world"

def test_evaluate_request_output_text_optional():
    req = EvaluateRequest(policy_id="p1", input_text="hello")
    assert req.output_text is None
