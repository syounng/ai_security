"use client";
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

const TYPE_GROUPS: { type: PolicyType; label: string; color: string }[] = [
  { type: "prompt_defense", label: "🛡️ 프롬프트 방어",  color: "text-blue-400 border-blue-900" },
  { type: "sensitive_data", label: "🔒 민감정보 보호",  color: "text-yellow-400 border-yellow-900" },
  { type: "content_safety", label: "⚠️ 콘텐츠 안전",   color: "text-orange-400 border-orange-900" },
  { type: "compliance",     label: "📋 컴플라이언스",   color: "text-purple-400 border-purple-900" },
];

export default function PolicyList({ policies, selectedId, onSelect, onDeploy, onRollback }: Props) {
  const grouped = TYPE_GROUPS.map(g => ({
    ...g,
    items: policies.filter(p => p.policy_type === g.type),
  })).filter(g => g.items.length > 0);

  if (policies.length === 0) {
    return (
      <div className="space-y-2">
        <h2 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">정책 목록</h2>
        <p className="text-gray-600 text-sm py-4 text-center">등록된 정책이 없습니다.</p>
      </div>
    );
  }

  return (
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
  );
}
