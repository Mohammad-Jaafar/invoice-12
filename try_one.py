import sys
from pathlib import Path

from app.extractor import extract_file

path = Path(sys.argv[1])
invoice, usage = extract_file(path)
out = Path("data/out")
out.mkdir(parents=True, exist_ok=True)
(out / f"{path.stem}.json").write_text(
    invoice.model_dump_json(indent=2), encoding="utf-8"
)
print(invoice.model_dump_json(indent=2))
print(usage)
