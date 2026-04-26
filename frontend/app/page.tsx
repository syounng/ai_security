"use client";
import { useState, useEffect, useCallback } from "react";
import { api, Policy, Rule, AuditEntry, Diff } from "@/lib/api";
import PolicyEditor from "@/components/PolicyEditor";
import TestHarness from "@/components/TestHarness";
import PolicyList from "@/components/PolicyList";
import AuditLog from "@/components/AuditLog";
import DiffViewer from "@/components/DiffViewer";

type Tab = "editor" | "test" | "audit";

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
    await api.deployPolicy(p.id);
    refreshPolicies();
    refreshAudit();
    if (selectedPolicy?.id === p.id) {
      const updated = await api.getPolicy(p.id);
      setSelectedPolicy(updated.policy);
    }
  };

  const handleRollback = async (p: Policy) => {
    await api.rollbackPolicy(p.id);
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
