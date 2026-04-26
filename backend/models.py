from pydantic import BaseModel
from typing import Literal, Optional, List

POLICY_TYPE = Literal["prompt_defense", "sensitive_data", "content_safety", "compliance"]


class RuleCondition(BaseModel):
    type: Literal["category", "contains", "regex"]
    value: str


class Rule(BaseModel):
    id: str
    policy_id: str
    action: Literal["block", "mask", "approval", "pass"]
    condition: RuleCondition
    description: str


class Policy(BaseModel):
    id: str
    name: str
    natural_language: str
    policy_type: POLICY_TYPE = "content_safety"
    rule_ids: List[str]
    previous_rule_ids: List[str] = []
    status: Literal["draft", "active", "inactive"]
    version: int
    created_at: str
    updated_at: str


class CreatePolicyRequest(BaseModel):
    name: str
    natural_language: str
    change_reason: str = "최초 생성"
    policy_type: POLICY_TYPE = "content_safety"


class UpdatePolicyRequest(BaseModel):
    natural_language: str
    change_reason: str


class EvaluateRequest(BaseModel):
    policy_id: str
    input_text: str
    output_text: Optional[str] = None


class TestResult(BaseModel):
    input_text: str
    matched_rules: List[str]
    action: Literal["blocked", "masked", "approval_required", "passed"]
    reason: str
    explanation: str


class AuditEntry(BaseModel):
    policy_id: str
    policy_name: str
    version_from: Optional[int]
    version_to: int
    changed_by: str
    change_reason: str
    timestamp: str


class PreviewPolicyRequest(BaseModel):
    natural_language: str
