import re

from pydantic import BaseModel

from app.schema import Invoice

TOLERANCE = 0.02
VAT_RATE = 0.05
ARABIC_INDIC_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")


class ValidationResult(BaseModel):
    status: str
    problems: list[str]


def normalize_digits(value: str) -> str:
    return value.translate(ARABIC_INDIC_DIGITS)


def close(a: float, b: float) -> bool:
    return abs(a - b) <= TOLERANCE


def validate(invoice: Invoice) -> ValidationResult:
    problems = []
    for number, item in enumerate(invoice.items, start=1):
        expected = item.quantity * item.unit_price
        if not close(expected, item.line_total):
            problems.append(
                f"item{number}: quantity * unit_price {expected:.2f}"
                f" != line_total {item.line_total:.2f}"
            )
    items_total = sum(item.line_total for item in invoice.items)
    if not close(items_total, invoice.subtotal):
        problems.append(
            f"sum of line totals {items_total:.2f} != subtotal {invoice.subtotal:.2f}"
        )
    expected_vat = invoice.subtotal * VAT_RATE
    if not close(expected_vat, invoice.vat_amount):
        problems.append(
            f"vat_amount {invoice.vat_amount:.2f} != 5% of subtotal {expected_vat:.2f}"
        )
    if not close(invoice.subtotal + invoice.vat_amount, invoice.total):
        problems.append(
            f"subtotal + vat_amount {invoice.subtotal + invoice.vat_amount:.2f}"
            f" != total {invoice.total:.2f}"
        )
    if invoice.supplier_trn is not None:
        trn = normalize_digits(invoice.supplier_trn).replace(" ", "").replace("-", "")
        if not re.fullmatch(r"[0-9]{15}", trn):
            problems.append(f"supplier_trn {invoice.supplier_trn!r} is not 15 digits")
    status = "needs_review" if problems else "ok"
    return ValidationResult(status=status, problems=problems)
