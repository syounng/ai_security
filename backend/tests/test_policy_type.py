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

import llm_client

def test_translate_uses_prompt_defense_prompt():
    assert "prompt_defense" in llm_client._PROMPTS_BY_TYPE
    assert "sensitive_data" in llm_client._PROMPTS_BY_TYPE
    assert "content_safety" in llm_client._PROMPTS_BY_TYPE
    assert "compliance" in llm_client._PROMPTS_BY_TYPE

def test_translate_signature_accepts_policy_type():
    import inspect
    sig = inspect.signature(llm_client.translate_natural_language)
    assert "policy_type" in sig.parameters

import storage as storage_mod
import json as json_mod
import tempfile
import os as os_mod

def test_create_policy_stores_policy_type(monkeypatch, tmp_path):
    data_file = tmp_path / "policies.json"
    data_file.write_text(json_mod.dumps({"policies": [], "rules": []}))
    monkeypatch.setattr(storage_mod, "POLICIES_FILE", data_file)

    policy, rules = storage_mod.create_policy(
        name="test",
        natural_language="block injection",
        rules_data=[{"action": "block", "condition": {"type": "category", "value": "prompt_injection"}, "description": "test"}],
        policy_type="prompt_defense",
    )
    assert policy.policy_type == "prompt_defense"

    saved = json_mod.loads(data_file.read_text())
    assert saved["policies"][0]["policy_type"] == "prompt_defense"
