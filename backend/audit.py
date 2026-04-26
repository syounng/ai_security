import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from models import AuditEntry

AUDIT_FILE = Path(__file__).parent.parent / "data" / "audit.jsonl"


def append(entry: AuditEntry) -> None:
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def get_all(limit: int = 50) -> List[AuditEntry]:
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = []
    for line in lines:
        if line:
            try:
                entries.append(AuditEntry(**json.loads(line)))
            except (json.JSONDecodeError, Exception):
                continue
    return list(reversed(entries))[:limit]


def get_by_group(group_id: str, limit: int = 50) -> List[AuditEntry]:
    return [e for e in get_all(limit=200) if e.policy_group_id == group_id][:limit]


def record(
    policy_group_id: str,
    policy_name: str,
    version_from: Optional[int],
    version_to: int,
    change_reason: str,
    changed_by: str = "operator",
) -> AuditEntry:
    entry = AuditEntry(
        policy_group_id=policy_group_id,
        policy_name=policy_name,
        version_from=version_from,
        version_to=version_to,
        changed_by=changed_by,
        change_reason=change_reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    append(entry)
    return entry
