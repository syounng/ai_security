"use client";
import { Diff, Rule } from "@/lib/api";

type Props = { diff: Diff | null };

const ACTION_KO: Record<string, string> = {
  block: "차단", mask: "마스킹", approval: "승인 필요", pass: "통과",
};

function RuleRow({ rule, type }: { rule: Rule; type: "added" | "removed" | "unchanged" }) {
  const styles = {
    added:     "bg-green-900/30 border-green-700 text-green-300",
    removed:   "bg-red-900/30 border-red-700 text-red-300 opacity-60",
    unchanged: "bg-gray-800 border-gray-700 text-gray-500",
  };
  const prefix = { added: "+", removed: "−", unchanged: " " };

  return (
    <div className={`border rounded px-3 py-2 text-xs font-mono flex gap-2 ${styles[type]}`}>
      <span className="w-3 flex-shrink-0 font-bold">{prefix[type]}</span>
      <span>
        <span className="font-semibold">{ACTION_KO[rule.action] ?? rule.action}</span>
        {" | "}
        {rule.condition.type}:{rule.condition.value}
        {rule.description ? ` — ${rule.description}` : ""}
      </span>
    </div>
  );
}

export default function DiffViewer({ diff }: Props) {
  if (!diff) return null;
  const hasChanges = diff.added.length > 0 || diff.removed.length > 0;

  return (
    <div className="space-y-2 border-t border-gray-700 pt-4">
      <div className="flex items-center gap-2">
        <h3 className="text-sm font-semibold text-gray-300">Rule Diff</h3>
        {!hasChanges && <span className="text-xs text-gray-600">(변경 없음)</span>}
        {hasChanges && (
          <span className="text-xs text-gray-500">
            +{diff.added.length} / -{diff.removed.length}
          </span>
        )}
      </div>
      <div className="space-y-1">
        {diff.removed.map((r, i) => <RuleRow key={`r-${i}`} rule={r} type="removed" />)}
        {diff.added.map((r, i) => <RuleRow key={`a-${i}`} rule={r} type="added" />)}
        {diff.unchanged.map((r, i) => <RuleRow key={`u-${i}`} rule={r} type="unchanged" />)}
      </div>
    </div>
  );
}
