"use client";
import { useState, useEffect, useCallback } from "react";
import { api, Policy, Rule, AuditEntry, Diff } from "@/lib/api";
import PolicyEditor from "@/components/PolicyEditor";
import TestHarness from "@/components/TestHarness";
import PolicyList from "@/components/PolicyList";
import AuditLog from "@/components/AuditLog";
import DiffViewer from "@/components/DiffViewer";

type Tab = "editor" | "test" | "audit";

const TYPE_META: Record<string, { label: string; color: string }> = {
  prompt_defense: { label: "🛡️ 프롬프트 방어", color: "text-blue-300 border-blue-700 bg-blue-950/30" },
  sensitive_data: { label: "🔒 민감정보 보호", color: "text-yellow-300 border-yellow-700 bg-yellow-950/30" },
  content_safety: { label: "⚠️ 콘텐츠 안전",  color: "text-orange-300 border-orange-700 bg-orange-950/30" },
  compliance:     { label: "📋 컴플라이언스", color: "text-purple-300 border-purple-700 bg-purple-950/30" },
};

export default function Home() {
  const [policies, setPolicies] = useState<Policy[]>([]);
  const [selectedPolicy, setSelectedPolicy] = useState<Policy | null>(null);
  const [auditEntries, setAuditEntries] = useState<AuditEntry[]>([]);
  const [lastDiff, setLastDiff] = useState<Diff | null>(null);
  const [activeTab, setActiveTab] = useState<Tab>("editor");
  const [backendError, setBackendError] = useState(false);

  const refreshPolicies = useCallback(async () => {
    try {
      const ps = await api.listPolicies();
      setPolicies(ps);
      setBackendError(false);
    } catch {
      setBackendError(true);
    }
  }, []);

  const refreshAudit = useCallback(async () => {
    try {
      const entries = await api.getAuditLogs();
      setAuditEntries(entries);
    } catch { /* silent */ }
  }, []);

  useEffect(() => {
    refreshPolicies();
    refreshAudit();
  }, [refreshPolicies, refreshAudit]);

  const handleCreated = (policy: Policy, _rules: Rule[]) => {
    refreshPolicies();
    refreshAudit();
    setSelectedPolicy(policy);
    setLastDiff(null);
    setActiveTab("test");
  };

  const handleUpdated = (policy: Policy, _rules: Rule[], diff?: Diff) => {
    refreshPolicies();
    refreshAudit();
    setSelectedPolicy(policy);
    setLastDiff(diff ?? null);
  };

  const handleDeploy = async (p: Policy) => {
    const updated = await api.deployPolicy(p.policy_group_id, p.version);
    refreshPolicies();
    refreshAudit();
    if (selectedPolicy?.policy_group_id === p.policy_group_id) {
      setSelectedPolicy(updated);
    }
  };

  const handleRollback = async (p: Policy) => {
    const updated = await api.rollbackPolicy(p.policy_group_id);
    refreshPolicies();
    refreshAudit();
    if (selectedPolicy?.policy_group_id === p.policy_group_id) {
      setSelectedPolicy(updated);
    }
  };

  const handleToDraft = async (p: Policy) => {
    await api.toDraftPolicy(p.id);
    refreshPolicies();
    refreshAudit();
    if (selectedPolicy?.id === p.id) {
      const updated = await api.getPolicy(p.id);
      setSelectedPolicy(updated.policy);
    }
  };

  const selectPolicy = (p: Policy) => {
    setSelectedPolicy(p);
    setLastDiff(null);
    setActiveTab("editor");
  };

  const tabs: { key: Tab; label: string }[] = [
    { key: "editor", label: "정책 편집" },
    { key: "test",   label: "테스트" },
    { key: "audit",  label: "Audit Log" },
  ];

  return (
    <div className="min-h-screen bg-[#0f1117] flex flex-col">
      {/* 헤더 */}
      <header className="border-b border-gray-800 px-6 py-3 flex items-center gap-3 flex-shrink-0">
        <span className="text-indigo-400 text-xl">🛡️</span>
        <h1 className="text-base font-bold text-gray-100">Guardrail Control Plane</h1>
        <span className="text-xs text-gray-600 ml-1">AI Safety Policy Manager</span>
        {backendError && (
          <span className="ml-auto text-xs text-red-400 bg-red-900/30 border border-red-800 rounded px-2 py-0.5">
            백엔드 연결 실패 — uvicorn main:app 실행 필요
          </span>
        )}
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* 사이드바 */}
        <aside className="w-64 border-r border-gray-800 flex flex-col flex-shrink-0">
          <div className="flex-1 overflow-y-auto p-3 space-y-2">
            <PolicyList
              policies={policies}
              selectedId={selectedPolicy?.id ?? null}
              onSelect={selectPolicy}
              onDeploy={handleDeploy}
              onRollback={handleRollback}
            />
          </div>
          <div className="p-3 border-t border-gray-800">
            <button
              onClick={() => { setSelectedPolicy(null); setLastDiff(null); setActiveTab("editor"); }}
              className="w-full text-xs bg-indigo-900/40 hover:bg-indigo-800/50 text-indigo-300 border border-indigo-800 rounded px-3 py-2 transition-colors"
            >
              + 새 정책 만들기
            </button>
          </div>
        </aside>

        {/* 메인 */}
        <main className="flex-1 flex flex-col overflow-hidden">
          {/* 탭 */}
          <div className="flex gap-0 border-b border-gray-800 flex-shrink-0">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-5 py-2.5 text-sm font-medium border-b-2 transition-colors ${
                  activeTab === tab.key
                    ? "border-indigo-500 text-indigo-300 bg-gray-900"
                    : "border-transparent text-gray-500 hover:text-gray-300"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* 탭 콘텐츠 */}
          <div className="flex-1 overflow-y-auto p-6">
            {activeTab === "editor" && (
              <div className="max-w-2xl space-y-4">
                {selectedPolicy && (
                  <div className="bg-gray-900 border border-gray-700 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-3">
                      <span className="text-sm text-gray-400 font-medium">현재 상태</span>
                      {selectedPolicy.status === "active" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-900/50 text-green-300 border border-green-700">
                          운영중 (active)
                        </span>
                      )}
                      {selectedPolicy.status === "draft" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-900/50 text-yellow-300 border border-yellow-700">
                          작업중 (draft)
                        </span>
                      )}
                      {selectedPolicy.status === "inactive" && (
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-900/50 text-red-300 border border-red-700">
                          롤백됨 (inactive)
                        </span>
                      )}
                      <span className="text-xs text-gray-600 ml-auto">v{selectedPolicy.version}</span>
                      {TYPE_META[selectedPolicy.policy_type] && (
                        <span className={`px-2 py-0.5 rounded border text-xs font-medium ${TYPE_META[selectedPolicy.policy_type].color}`}>
                          {TYPE_META[selectedPolicy.policy_type].label}
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 space-y-1">
                      <p><span className="text-gray-600">draft</span> — 작업 중인 초안. 아직 운영에 적용되지 않음.</p>
                      <p><span className="text-gray-600">active</span> — 현재 운영 중인 정책. 모든 요청에 적용됨.</p>
                      <p><span className="text-gray-600">inactive</span> — 롤백된 비활성 상태. 요청에 적용되지 않음.</p>
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      {selectedPolicy.status === "draft" && (
                        <button
                          onClick={() => handleDeploy(selectedPolicy)}
                          className="text-xs bg-green-800/50 hover:bg-green-700/60 text-green-300 border border-green-700 rounded px-3 py-1.5 transition-colors"
                        >
                          🚀 배포 (active 전환)
                        </button>
                      )}
                      {selectedPolicy.status === "active" && (
                        <>
                          <button
                            onClick={() => handleRollback(selectedPolicy)}
                            className="text-xs bg-red-900/40 hover:bg-red-800/50 text-red-300 border border-red-700 rounded px-3 py-1.5 transition-colors"
                          >
                            ⏪ 롤백 (inactive 전환)
                          </button>
                          <button
                            onClick={() => handleToDraft(selectedPolicy)}
                            className="text-xs bg-yellow-900/40 hover:bg-yellow-800/50 text-yellow-300 border border-yellow-700 rounded px-3 py-1.5 transition-colors"
                          >
                            📝 초안으로 (draft 전환)
                          </button>
                        </>
                      )}
                      {selectedPolicy.status === "inactive" && (
                        <>
                          <button
                            onClick={() => handleDeploy(selectedPolicy)}
                            className="text-xs bg-green-800/50 hover:bg-green-700/60 text-green-300 border border-green-700 rounded px-3 py-1.5 transition-colors"
                          >
                            🚀 재배포 (active 전환)
                          </button>
                          <button
                            onClick={() => handleToDraft(selectedPolicy)}
                            className="text-xs bg-yellow-900/40 hover:bg-yellow-800/50 text-yellow-300 border border-yellow-700 rounded px-3 py-1.5 transition-colors"
                          >
                            📝 초안으로 (draft 전환)
                          </button>
                        </>
                      )}
                    </div>
                  </div>
                )}
                <PolicyEditor
                  selectedPolicy={selectedPolicy}
                  onCreated={handleCreated}
                  onUpdated={handleUpdated}
                />
                {lastDiff && <DiffViewer diff={lastDiff} />}
              </div>
            )}
            {activeTab === "test" && (
              <div className="max-w-2xl">
                <TestHarness selectedPolicy={selectedPolicy} />
              </div>
            )}
            {activeTab === "audit" && (
              <div className="max-w-2xl">
                <AuditLog entries={auditEntries} />
              </div>
            )}
          </div>
        </main>
      </div>
    </div>
  );
}
