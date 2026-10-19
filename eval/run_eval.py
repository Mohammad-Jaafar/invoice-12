import argparse
import json
import time
from pathlib import Path

from app.extractor import MEDIA_TYPES, MODEL, extract_file
from app.schema import Invoice
from app.validator import validate
from eval.prices import cost
from eval.score import FIELDS, score_invoice

LANGUAGES = ["en", "ar", "mixed"]
RUNS = Path("eval/runs")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dir", type=Path, required=True)
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def language_of(path: Path) -> str:
    return path.stem.split("_")[2]


def evaluate(path: Path, model: str) -> dict:
    record = {"file": path.name, "language": language_of(path)}
    expected = Invoice.model_validate_json(
        path.with_suffix(".json").read_text(encoding="utf-8")
    )
    start = time.perf_counter()
    try:
        invoice, usage = extract_file(path, model)
    except Exception as error:
        record["error"] = f"{type(error).__name__}: {error}"
        record["fields"] = {field: False for field in FIELDS}
        record["correct"] = False
        return record
    record["seconds"] = round(time.perf_counter() - start, 2)
    record.update(usage)
    record["fields"] = score_invoice(expected, invoice)
    record["correct"] = all(record["fields"].values())
    record["status"] = validate(invoice).status
    record["invoice"] = invoice.model_dump(mode="json")
    return record


def percent(part: int, whole: int) -> str:
    return f"{100 * part / whole:.0f}%" if whole else "n/a"


def average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def summarize(records: list[dict], model: str, directory: Path) -> None:
    done = [r for r in records if "error" not in r]
    print(
        f"model={model} dir={directory.as_posix()} "
        f"invoices={len(records)} errors={len(records) - len(done)}"
    )
    for field in FIELDS:
        right = sum(r["fields"][field] for r in records)
        print(f"{field:<18} {percent(right, len(records))}")
    print(f"{'fully correct':<18} {percent(sum(r['correct'] for r in records), len(records))}")
    for language in LANGUAGES:
        group = [r for r in records if r["language"] == language]
        right = sum(r["correct"] for r in group)
        print(
            f"  fully correct [{language}]  {percent(right, len(group))}"
            f"  ({len(group)} invoices)"
        )
    wrong = [r for r in done if not r["correct"]]
    correct = [r for r in done if r["correct"]]
    flagged_wrong = sum(r["status"] == "needs_review" for r in wrong)
    flagged_correct = sum(r["status"] == "needs_review" for r in correct)
    print(f"wrong invoices flagged by validator: {flagged_wrong}/{len(wrong)}")
    print(f"correct invoices flagged by mistake: {flagged_correct}/{len(correct)}")
    seconds = average([r["seconds"] for r in done])
    tokens_in = average([r["input_tokens"] for r in done])
    tokens_out = average([r["output_tokens"] for r in done])
    print(f"avg seconds: {seconds:.1f}")
    print(f"avg tokens in/out: {tokens_in:.0f}/{tokens_out:.0f}")
    price = cost(model, tokens_in, tokens_out)
    if price is None:
        print(f"cost per invoice: unknown (no price for {model})")
    else:
        print(f"cost per invoice: ${price:.4f}")


def main() -> None:
    args = parse_args()
    images = sorted(p for p in args.dir.iterdir() if p.suffix.lower() in MEDIA_TYPES)
    records = [evaluate(path, args.model) for path in images[: args.limit]]
    summarize(records, args.model, args.dir)
    RUNS.mkdir(parents=True, exist_ok=True)
    out = RUNS / f"{args.model}__{args.dir.name}.json"
    run = {"model": args.model, "dir": args.dir.as_posix(), "records": records}
    out.write_text(json.dumps(run, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"saved to {out.as_posix()}")


if __name__ == "__main__":
    main()
