import argparse
from pathlib import Path

from app.extractor import MEDIA_TYPES, MODEL, extract_file
from app.validator import validate


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--model", default=MODEL)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    images = sorted(p for p in args.dir.iterdir() if p.suffix.lower() in MEDIA_TYPES)
    for path in images:
        try:
            invoice, _ = extract_file(path, args.model)
        except Exception as error:
            print(f"{path.name}: error {type(error).__name__}: {error}")
            continue
        (args.out / f"{path.stem}.json").write_text(
            invoice.model_dump_json(indent=2), encoding="utf-8"
        )
        result = validate(invoice)
        line = f"{path.name}: {result.status}"
        if result.problems:
            line += " " + "; ".join(result.problems)
        print(line)


if __name__ == "__main__":
    main()
