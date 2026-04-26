const BASE = "http://localhost:8000";

export type RuleCondition = { type: "category" | "contains" | "regex"; value: string };
export type Rule = { id: string; policy_id: string; action: "block" | "mask" | "approval" | "pass"; condition: RuleCondition; description: string };
export type Policy = { id: string; name: string; natural_language: string; rule_ids: string[]; status: "draft" | "active" | "inactive"; version: number; created_at: string; updated_at: string };
export type TestResult = { input_text: string; matched_rules: string[]; action: "blocked" | "masked" | "approval_required" | "passed"; reason: string; explanation: string };
export type AuditEntry = { policy_id: string; policy_name: string; version_from: number | null; version_to: number; changed_by: string; change_reason: string; timestamp: string };
export type Diff = { added: Rule[]; removed: Rule[]; unchanged: Rule[] };

async function req<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
  }
  return res.json();
}

export const api = {
  listPolicies: () => req<Policy[]>("/policies"),

  getPolicy: (id: string) => req<{ policy: Policy; rules: Rule[] }>(`/policies/${id}`),

  createPolicy: (name: string, natural_language: string, change_reason: string) =>
    req<{ policy: Policy; rules: Rule[] }>("/policies", {
      method: "POST",
      body: JSON.stringify({ name, natural_language, change_reason }),
    }),

  updatePolicy: (id: string, natural_language: string, change_reason: string) =>
    req<{ policy: Policy; rules: Rule[]; diff: Diff }>(`/policies/${id}`, {
      method: "PUT",
      body: JSON.stringify({ natural_language, change_reason }),
    }),

  deployPolicy: (id: string) => req<Policy>(`/policies/${id}/deploy`, { method: "POST" }),

  rollbackPolicy: (id: string) => req<Policy>(`/policies/${id}/rollback`, { method: "POST" }),

  toDraftPolicy: (id: string) => req<Policy>(`/policies/${id}/to-draft`, { method: "POST" }),

  evaluate: (policy_id: string, input_text: string) =>
    req<TestResult>("/evaluate", {
      method: "POST",
      body: JSON.stringify({ policy_id, input_text }),
    }),

  getAuditLogs: () => req<AuditEntry[]>("/audit-logs"),
};
