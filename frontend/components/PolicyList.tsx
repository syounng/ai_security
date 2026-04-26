"use client";
import { useState } from "react";
import { Policy, PolicyType } from "@/lib/api";

type Props = {
  policies: Policy[];
  selectedId: string | null;
  onSelect: (p: Policy) => void;
  onDeploy: (p: Policy) => void;
  onRollback: (p: Policy) => void;
};

const STATUS_BADGE: Record<string, string> = {
  active:   "bg-green-800 text-green-300",
  draft:    "bg-gray-700 text-gray-400",
  inactive: "bg-red-900 text-red-400",
};

const TYPE_GROUPS: { type: PolicyType; label: string; short: string; color: string; activeClass: string }[] = [
  { type: "prompt_defense", label: "🛡️ 프롬프트 방어", short: "🛡️", color: "text-blue-400 border-blue-900",    activeClass: "bg-blue-900/40 border-blue-500 text-blue-300" },
  { type: "sensitive_data", label: "🔒 민감정보 보호", short: "🔒", color: "text-yellow-400 border-yellow-900", activeClass: "bg-yellow-900/40 border-yellow-500 text-yellow-300" },
  { type: "content_safety", label: "⚠️ 콘텐츠 안전",  short: "⚠️", color: "text-orange-400 border-orange-900", activeClass: "bg-orange-900/40 border-orange-500 text-orange-300" },
  { type: "compliance",     label: "📋 컴플라이언스",  short: "📋", color: "text-purple-400 border-purple-900", activeClass: "bg-purple-900/40 border-purple-500 text-purple-300" },
];

export default function PolicyList({ policies, selectedId, onSelect, onDeploy, onRollback }: Props) {
  const [activeFilter, setActiveFilter] = useState<PolicyType | null>(null);

  const filtered = activeFilter ? policies.filter(p => p.policy_type === activeFilter) : policies;

  const grouped = TYPE_GROUPS.map(g => ({
    ...g,
    items: filtered.filter(p => p.policy_type === g.type),
  })).filter(g => g.items.length > 0);

  const countByType = (type: PolicyType) => policies.filter(p => p.policy_type === type).length;

  return (
    <div className="space-y-3">
      {/* 필터 버튼 */}
      <div className="space-y-1.5">
        <p className="text-xs text-gray-500 font-medium">유형 필터</p>
        <div className="grid grid-cols-2 gap-1">
          <button
            onClick={() => setActiveFilter(null)}
            className={`text-xs rounded px-2 py-1 border transition-colors text-left ${
              activeFilter === null
                ? "bg-indigo-900/40 border-indigo-500 text-indigo-300"
                : "border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-400"
            }`}
          >
            전체 <span className="text-gray-600">({policies.length})</span>
          </button>
          {TYPE_GROUPS.map(g => (
            <button
              key={g.type}
              onClick={() => setActiveFilter(activeFilter === g.type ? null : g.type)}
              className={`text-xs rounded px-2 py-1 border transition-colors text-left truncate ${
                activeFilter === g.type
                  ? g.activeClass
                  : "border-gray-700 text-gray-500 hover:border-gray-500 hover:text-gray-400"
              }`}
            >
              {g.short} <span className="text-gray-600">({countByType(g.type)})</span>
            </button>
          ))}
        </div>
      </div>

      {/* 정책 목록 */}
      {policies.length === 0 ? (
        <p className="text-gray-600 text-sm py-4 text-center">등록된 정책이 없습니다.</p>
      ) : grouped.length === 0 ? (
        <p className="text-gray-600 text-sm py-4 text-center">해당 유형의 정책이 없습니다.</p>
      ) : (
        <div className="space-y-4">
          {grouped.map(group => (
            <div key={group.type}>
              <div className={`text-xs font-semibold mb-1.5 pb-1 border-b ${group.color}`}>
                {group.label}
              </div>
              <div className="space-y-1.5">
                {group.items.map(p => (
                  <div
                    key={p.id}
                    onClick={() => onSelect(p)}
                    className={`rounded p-2.5 border cursor-pointer transition-all ${
                      selectedId === p.id
                        ? "border-indigo-500 bg-indigo-950/50 shadow-sm shadow-indigo-900"
                        : "border-gray-700 bg-gray-800/50 hover:border-gray-500"
                    }`}
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-sm font-medium text-gray-100 truncate">{p.name}</span>
                      <span className={`text-xs px-1.5 py-0.5 rounded-full flex-shrink-0 ${STATUS_BADGE[p.status]}`}>
                        {p.status}
                      </span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5">
                      v{p.version} · {new Date(p.updated_at).toLocaleString("ko-KR", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}
                    </p>
                    <div className="flex gap-1.5 mt-1.5" onClick={e => e.stopPropagation()}>
                      {p.status !== "active" && (
                        <button
                          onClick={() => onDeploy(p)}
                          className="text-xs bg-green-800 hover:bg-green-700 text-green-200 rounded px-2 py-0.5 transition-colors"
                        >
                          배포
                        </button>
                      )}
                      {p.status === "active" && (
                        <button
                          onClick={() => onRollback(p)}
                          className="text-xs bg-red-900 hover:bg-red-800 text-red-200 rounded px-2 py-0.5 transition-colors"
                        >
                          롤백
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
