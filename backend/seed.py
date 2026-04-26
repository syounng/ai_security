"""데모용 초기 데이터 초기화 스크립트"""
from pathlib import Path
import json

DATA_DIR = Path(__file__).parent.parent / "data"

DATA_DIR.joinpath("policies.json").write_text(
    json.dumps({"policies": [], "rules": []}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)
DATA_DIR.joinpath("audit.jsonl").write_text("", encoding="utf-8")
print("데이터 초기화 완료")
