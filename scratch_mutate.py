from pathlib import Path

from app.schema import Invoice
from app.validator import validate

invoice = Invoice.model_validate_json(
    Path("data/clean/inv_000_en_classic.json").read_text(encoding="utf-8")
)
print(validate(invoice))
invoice.items[0].line_total += 5
print(validate(invoice))
