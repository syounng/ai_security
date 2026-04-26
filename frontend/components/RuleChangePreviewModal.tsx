"use client";
import { Diff, Rule } from "@/lib/api";

const ACTION_LABELS: Record<string, string> = {
  block: "🚫 차단",
  mask: "🔒 마스킹",
  approval: "👤 승인 필요",
  pass: "✅ 통과",
};

function RuleRow({ rule, highlight }: { rule: Rule; highlight: "added" | "removed" | "unchanged" }) {
  const bg = highlight === "added"
    ? "bg-green-900/30 border-green-700"
    : highlight === "removed"
    ? "bg-red-900/30 border-red-700 opacity-60"
    : "bg-gray-800 border-gray-700";

  const badge = highlight === "added"
    ? <span className="text-green-400 text-xs font-bold mr-2">+ 추가</span>
    : highlight === "removed"
    ? <span className="text-red-400 text-xs font-bold mr-2">- 삭제</span>
    : <span className="text-gray-500 text-xs font-bold mr-2">= 유지</span>;

  return (
    <div className={`rounded p-3 text-sm border ${bg}`}>
      <div className="flex items-center gap-2 flex-wrap">
        {badge}
        <span className="font-mono text-indigo-300 font-semibold">{ACTION_LABELS[rule.action] ?? rule.action}</span>
        <span className="text-gray-600">|</span>
        <span className="text-gray-300 font-mono text-xs">{rule.condition_type}:{rule.condition_value}</span>
      </div>
      {rule.description && <p className="text-gray-400 mt-1 text-xs">{rule.description}</p>}
    </div>
  );
}

type Props = {
  diff: Diff;
  proposedRules: Rule[];
  onConfirm: () => void;
  onCancel: () => void;
  loading?: boolean;
};

export default function RuleChangePreviewModal({ diff, proposedRules, onConfirm, onCancel, loading }: Props) {
  const hasChanges = diff.added.length > 0 || diff.removed.length > 0;

  return (
    <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-gray-900 border border-gray-700 rounded-lg w-full max-w-lg max-h-[80vh] flex flex-col shadow-2xl">
        <div className="p-4 border-b border-gray-700">
          <h3 className="text-base font-semibold text-gray-100">Gemini 룰 변경 추천</h3>
          <p className="text-xs text-gray-400 mt-1">
            {hasChanges
              ? `${diff.added.length}개 추가 · ${diff.removed.length}개 삭제 · ${diff.unchanged.length}개 유지`
              : "변경 사항이 없습니다."}
          </p>
        </div>

        <div className="overflow-y-auto flex-1 p-4 space-y-2">
          {diff.removed.map((rule, i) => <RuleRow key={`rm-${i}`} rule={rule as Rule} highlight="removed" />)}
          {diff.added.map((rule, i) => <RuleRow key={`add-${i}`} rule={rule as Rule} highlight="added" />)}
          {diff.unchanged.map((rule, i) => <RuleRow key={`unch-${i}`} rule={rule as Rule} highlight="unchanged" />)}
        </div>

        <div className="p-4 border-t border-gray-700 flex gap-3">
          <button
            onClick={onCancel}
            disabled={loading}
            className="flex-1 bg-gray-700 hover:bg-gray-600 disabled:opacity-50 text-gray-100 rounded px-4 py-2 text-sm font-medium transition-colors"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className="flex-1 bg-indigo-600 hover:bg-indigo-500 disabled:bg-gray-700 disabled:cursor-not-allowed text-white rounded px-4 py-2 text-sm font-medium transition-colors"
          >
            {loading ? "적용 중..." : "이대로 적용"}
          </button>
        </div>
      </div>
    </div>
  );
}
