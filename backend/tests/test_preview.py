import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from unittest.mock import patch
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

        from models import Policy, Rule
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
