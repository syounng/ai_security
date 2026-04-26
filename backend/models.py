from pydantic import BaseModel
from typing import Literal, Optional, List

PolicyType = Literal["prompt_defense", "sensitive_data", "content_safety", "compliance"]


class Rule(BaseModel):
    id: str
    policy_id: str
    action: Literal["block", "mask", "approval", "pass"]
    condition_type: Literal["category", "contains", "regex"]
    condition_value: str
    description: str


class Policy(BaseModel):
    id: str
    policy_group_id: str
    name: str
    natural_language: str
    policy_type: PolicyType = "content_safety"
    status: Literal["draft", "active", "archived"]
    version: int
    created_at: str


class CreatePolicyRequest(BaseModel):
    name: str
    natural_language: str
    change_reason: str = "최초 생성"
    policy_type: PolicyType = "content_safety"


class ReviseRequest(BaseModel):
    natural_language: str
    change_reason: str


class EvaluateRequest(BaseModel):
    policy_id: str
    input_text: str


class TestResult(BaseModel):
    input_text: str
    matched_rules: List[str]
    action: Literal["blocked", "masked", "approval_required", "passed"]
    reason: str
    explanation: str
    translation_source: str
    gemini_error: bool = False


class AuditEntry(BaseModel):
    policy_group_id: str
    policy_name: str
    version_from: Optional[int]
    version_to: int
    changed_by: str
    change_reason: str
    timestamp: str
