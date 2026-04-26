import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List
from models import AuditEntry

AUDIT_FILE = Path(__file__).parent.parent / "data" / "audit.jsonl"


def append(entry: AuditEntry) -> None:
    with AUDIT_FILE.open("a", encoding="utf-8") as f:
        f.write(entry.model_dump_json() + "\n")


def get_all(limit: int = 50) -> List[AuditEntry]:
    if not AUDIT_FILE.exists():
        return []
    lines = AUDIT_FILE.read_text(encoding="utf-8").strip().splitlines()
    entries = [AuditEntry(**json.loads(line)) for line in lines if line]
    return list(reversed(entries))[:limit]


def record(
    policy_id: str,
    policy_name: str,
    version_from: Optional[int],
    version_to: int,
    change_reason: str,
    changed_by: str = "operator",
) -> AuditEntry:
    entry = AuditEntry(
        policy_id=policy_id,
        policy_name=policy_name,
        version_from=version_from,
        version_to=version_to,
        changed_by=changed_by,
        change_reason=change_reason,
        timestamp=datetime.now(timezone.utc).isoformat(),
    )
    append(entry)
    return entry
