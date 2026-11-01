import argparse
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import defer

from app.db import SessionLocal
from app.models import Extraction
from app.schema import Invoice
from eval.run_eval import summarize
from eval.score import score_invoice


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tag", default="real")
    return parser.parse_args()


def collect(tag: str) -> dict:
    with SessionLocal() as session:
        extractions = session.scalars(
            select(Extraction)
            .options(defer(Extraction.image))
            .where(Extraction.tag == tag, Extraction.reviewed_data.is_not(None))
            .order_by(Extraction.id)
        ).all()
        rows = []
        for extraction in extractions:
            fields = score_invoice(
                Invoice.model_validate(extraction.reviewed_data),
                Invoice.model_validate(extraction.data),
            )
            rows.append(
                {
                    "file": extraction.filename,
                    "language": "unknown",
                    "fields": fields,
                    "correct": all(fields.values()),
                    "status": extraction.status,
                    "problems": extraction.problems,
                    "input_tokens": extraction.input_tokens,
                    "output_tokens": extraction.output_tokens,
                    "seconds": extraction.seconds,
                }
            )
        model = extractions[0].model if extractions else "none"
    return {
        "model": model,
        "directory": f"database tag={tag} (reviewed only)",
        "rows": rows,
    }


def main() -> None:
    args = parse_args()
    result = collect(args.tag)
    summarize(result["rows"], result["model"], Path(result["directory"]))


if __name__ == "__main__":
    main()
