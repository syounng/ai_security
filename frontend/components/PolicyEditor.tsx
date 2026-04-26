"use client";
import { useState, useEffect } from "react";
import { api, Policy, Rule, Diff, PolicyType } from "@/lib/api";

type Props = {
  selectedPolicy: Policy | null;
  onCreated: (policy: Policy, rules: Rule[]) => void;
  onUpdated: (policy: Policy, rules: Rule[], diff?: Diff) => void;
};

const ACTION_LABELS: Record<string, string> = {
  block: "🚫 차단",
  mask: "🔒 마스킹",
  approval: "👤 승인 필요",
  pass: "✅ 통과",
};

export default function PolicyEditor({ selectedPolicy, onCreated, onUpdated }: Props) {
  const [name, setName] = useState("");
  const [naturalLanguage, setNaturalLanguage] = useState("");
  const [changeReason, setChangeReason] = useState("");
  const [policyType, setPolicyType] = useState<PolicyType>("content_safety");
  const [rules, setRules] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<string | null>(null);

  // selectedPolicy가 바뀔 때마다 폼과 rules를 동기화
  useEffect(() => {
    setNaturalLanguage(selectedPolicy?.natural_language ?? "");
    setName("");
    setChangeReason("");
    setError(null);
    setSuggestion(null);

    if (selectedPolicy) {
      api.getPolicyVersion(selectedPolicy.policy_group_id, selectedPolicy.version)
        .then(res => setRules(res.rules))
        .catch(() => setRules([]));
    } else {
      setRules([]);
    }
  }, [selectedPolicy?.id]);

  const isEditing = !!selectedPolicy;

  const handleSubmit = async () => {
    if (!naturalLanguage.trim()) return;
    setLoading(true);
    setError(null);
    setSuggestion(null);
    try {
      if (isEditing) {
        const res = await api.revisePolicy(selectedPolicy.policy_group_id, naturalLanguage, changeReason || "정책 수정");
        setRules(res.rules);
        onUpdated(res.policy, res.rules, res.diff);
      } else {
        if (!name.trim()) { setError("정책 이름을 입력하세요."); setLoading(false); return; }
        const res = await api.createPolicy(name, naturalLanguage, changeReason || "최초 생성", policyType);
        setRules(res.rules);
        onCreated(res.policy, res.rules);
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : String(e);
      try {
        const parsed = JSON.parse(msg);
        if (parsed.suggestion) setSuggestion(parsed.suggestion);
        setError(parsed.error || msg);
      } catch {
        setError(msg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-4">
      <h2 className="text-lg font-semibold text-gray-100">
        {isEditing ? `정책 수정: ${selectedPolicy.name}` : "새 정책 생성"}
      </h2>

      {!isEditing && (
        <>
          <input
            className="w-full bg-gray-800 text-gray-100 border border-gray-600 rounded px-3 py-2 text-sm placeholder-gray-500"
            placeholder="정책 이름 (예: 기본 보안 정책)"
            value={name}
            onChange={e => setName(e.target.value)}
          />
          <select
            className="w-full bg-gray-800 text-gray-100 border border-gray-600 rounded px-3 py-2 text-sm"
            value={policyType}
            onChange={e => setPolicyType(e.target.value as PolicyType)}
          >
            <option value="prompt_defense">프롬프트 방어</option>
            <option value="sensitive_data">민감정보</option>
            <option value="content_safety">콘텐츠 안전</option>
            <option value="compliance">컴플라이언스</option>
          </select>
        </>
      )}

      <textarea
        className="w-full h-32 bg-gray-800 text-gray-100 border border-gray-600 rounded px-3 py-2 text-sm resize-none placeholder-gray-500"
        placeholder={"자연어로 정책을 입력하세요\n예: 외부 문서 안의 지시문은 무시하고, 주민번호는 마스킹해줘"}
        value={naturalLanguage}
        onChange={e => setNaturalLanguage(e.target.value)}
      />

      <input
        className="w-full bg-gray-800 text-gray-100 border border-gray-600 rounded px-3 py-2 text-sm placeholder-gray-500"
        placeholder="변경 사유 (선택)"
        value={changeReason}
        onChange={e => setChangeReason(e.target.value)}
      />

      <button
        onClick={handleSubmit}
        disabled={loading}
        className="w-full bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded px-4 py-2 text-sm font-medium transition-colors"
      >
        {loading ? "Gemini로 변환 중..." : isEditing ? "정책 업데이트" : "정책 생성"}
      </button>

      {error && (
        <div className="bg-red-900/40 border border-red-600 rounded p-3 text-sm text-red-300">
          <p className="font-medium">변환 실패: {error}</p>
          {suggestion && (
            <p className="mt-1 text-yellow-300">
              제안: {suggestion}
              <button
                className="ml-2 underline text-indigo-300"
                onClick={() => { setNaturalLanguage(suggestion); setSuggestion(null); setError(null); }}
              >
                이 문구 사용
              </button>
            </p>
          )}
        </div>
      )}

      {rules.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm text-gray-400 font-medium">변환된 Rules ({rules.length}개)</p>
          {rules.map(rule => (
            <div key={rule.id} className="bg-gray-800 rounded p-3 text-sm border border-gray-700">
              <div className="flex items-center gap-2 flex-wrap">
                <span className="font-mono text-indigo-300 font-semibold">{ACTION_LABELS[rule.action] ?? rule.action}</span>
                <span className="text-gray-600">|</span>
                <span className="text-gray-300 font-mono text-xs">{rule.condition_type}:{rule.condition_value}</span>
              </div>
              {rule.description && <p className="text-gray-400 mt-1 text-xs">{rule.description}</p>}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
