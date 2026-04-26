const BASE = "http://localhost:8000";

export type PolicyType = "prompt_defense" | "sensitive_data" | "content_safety" | "compliance";

export type Rule = {
  id: string;
  policy_id: string;
  action: "block" | "mask" | "approval" | "pass";
  condition_type: "category" | "contains" | "regex";
  condition_value: string;
  description: string;
};

export type Policy = {
  id: string;
  policy_group_id: string;
  name: string;
  natural_language: string;
  policy_type: PolicyType;
  status: "draft" | "active" | "archived";
  version: number;
  created_at: string;
};

export type TestResult = {
  input_text: string;
  matched_rules: string[];
  action: "blocked" | "masked" | "approval_required" | "passed";
  reason: string;
  explanation: string;
  translation_source: string;
  gemini_error: boolean;
};

export type AuditEntry = {
  policy_group_id: string;
  policy_name: string;
  version_from: number | null;
  version_to: number;
  changed_by: string;
  change_reason: string;
  timestamp: string;
};

export type Diff = {
  added: Rule[];
  removed: Rule[];
  unchanged: Rule[];
};

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(
      typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail)
    );
  }
  return res.json();
}

export const api = {
  listPolicies: () => req<Policy[]>("/policies"),

  getPolicyVersions: (groupId: string) =>
    req<Policy[]>(`/policies/${groupId}/versions`),

  getPolicyVersion: (groupId: string, version: number) =>
    req<{ policy: Policy; rules: Rule[] }>(
      `/policies/${groupId}/versions/${version}`
    ),

  createPolicy: (name: string, natural_language: string, change_reason: string, policy_type: PolicyType = "content_safety") =>
    req<{ policy: Policy; rules: Rule[]; translation_source: string }>(
      "/policies",
      { method: "POST", body: JSON.stringify({ name, natural_language, change_reason, policy_type }) }
    ),

  revisePolicy: (groupId: string, natural_language: string, change_reason: string) =>
    req<{ policy: Policy; rules: Rule[]; diff: Diff; translation_source: string }>(
      `/policies/${groupId}/revise`,
      { method: "POST", body: JSON.stringify({ natural_language, change_reason }) }
    ),

  getDiff: (groupId: string, fromV: number, toV: number) =>
    req<Diff>(`/policies/${groupId}/diff?from_v=${fromV}&to_v=${toV}`),

  deployPolicy: (groupId: string, version: number) =>
    req<Policy>(`/policies/${groupId}/versions/${version}/deploy`, { method: "POST" }),

  rollbackPolicy: (groupId: string) =>
    req<Policy>(`/policies/${groupId}/rollback`, { method: "POST" }),

  evaluate: (policy_id: string, input_text: string) =>
    req<TestResult>("/evaluate", {
      method: "POST",
      body: JSON.stringify({ policy_id, input_text }),
    }),

  getAuditLogs: () => req<AuditEntry[]>("/audit-logs"),

  getAuditLogsForGroup: (groupId: string) =>
    req<AuditEntry[]>(`/audit-logs/${groupId}`),
};
