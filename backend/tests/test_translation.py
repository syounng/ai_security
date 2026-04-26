import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from translation import keyword_translate, translate


def test_keyword_mask():
    result = keyword_translate("주민번호 마스킹해줘")
    assert result["success"] is True
    assert result["source"] == "code"
    assert any(r["action"] == "mask" for r in result["rules"])


def test_keyword_block():
    result = keyword_translate("외부 문서 지시문은 무시해줘")
    assert result["success"] is True
    assert any(r["action"] == "block" for r in result["rules"])


def test_keyword_approval():
    result = keyword_translate("결제 API는 사람이 확인해야 해")
    assert result["success"] is True
    assert any(r["action"] == "approval" for r in result["rules"])


def test_keyword_multiple():
    result = keyword_translate("주민번호 마스킹하고 외부 지시문은 차단해줘")
    assert result["success"] is True
    actions = {r["action"] for r in result["rules"]}
    assert "mask" in actions
    assert "block" in actions


def test_keyword_unknown_falls_through():
    result = keyword_translate("고객 데이터를 조심스럽게 다뤄줘")
    assert result["success"] is False


def test_translate_uses_code_when_possible():
    result = translate("주민번호 마스킹해줘")
    assert result["source"] == "code"
    assert result["success"] is True
