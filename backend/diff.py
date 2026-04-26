from typing import List
from models import Rule


def _sig(rule: Rule) -> str:
    return f"{rule.action}:{rule.condition_type}:{rule.condition_value}"


def compute_diff(old_rules: List[Rule], new_rules: List[Rule]) -> dict:
    old_map = {_sig(r): r for r in old_rules}
    new_map = {_sig(r): r for r in new_rules}

    added = [r.model_dump() for sig, r in new_map.items() if sig not in old_map]
    removed = [r.model_dump() for sig, r in old_map.items() if sig not in new_map]
    unchanged = [r.model_dump() for sig, r in new_map.items() if sig in old_map]

    return {"added": added, "removed": removed, "unchanged": unchanged}
