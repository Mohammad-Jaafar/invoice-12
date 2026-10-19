import json
from pathlib import Path

from app.extractor import MODEL


def wrong(path):
    records = json.loads(Path(path).read_text(encoding="utf-8"))["records"]
    return {
        Path(r["file"]).stem: [k for k, v in r["fields"].items() if not v]
        for r in records
        if "error" not in r and not r["correct"]
    }


clean = wrong(f"eval/runs/{MODEL}__clean.json")
scanned = wrong(f"eval/runs/{MODEL}__scanned.json")
for name in sorted(set(clean) | set(scanned)):
    print(f"{name:<28} clean={clean.get(name, '-')}  scanned={scanned.get(name, '-')}")
