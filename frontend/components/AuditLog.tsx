"use client";
import { AuditEntry } from "@/lib/api";

type Props = { entries: AuditEntry[] };

export default function AuditLog({ entries }: Props) {
  return (
    <div className="space-y-3">
      <h2 className="text-lg font-semibold text-gray-100">Audit Log</h2>
      {entries.length === 0 && (
        <p className="text-gray-500 text-sm py-8 text-center">기록이 없습니다.</p>
      )}
      <div className="space-y-2 max-h-[60vh] overflow-y-auto pr-1">
        {entries.map((e, i) => (
          <div key={i} className="bg-gray-800 border border-gray-700 rounded p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <span className="text-sm font-medium text-gray-200">{e.policy_name}</span>
                <span className="ml-2 text-xs text-gray-500 font-mono">
                  {e.version_from !== null && e.version_from !== undefined
                    ? `v${e.version_from} → v${e.version_to}`
                    : `v${e.version_to} 생성`}
                </span>
              </div>
              <span className="text-xs text-gray-500 flex-shrink-0">
                {new Date(e.timestamp).toLocaleString("ko-KR", {
                  month: "numeric", day: "numeric",
                  hour: "2-digit", minute: "2-digit",
                })}
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-1">{e.change_reason}</p>
            <p className="text-xs text-gray-600 mt-0.5">by {e.changed_by}</p>
          </div>
        ))}
      </div>
    </div>
  );
}
