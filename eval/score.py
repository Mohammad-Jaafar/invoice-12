import re

from app.schema import Invoice, LineItem
from app.validator import normalize_digits

FIELDS = [
    "supplier_name",
    "supplier_trn",
    "invoice_number",
    "invoice_date",
    "currency",
    "items",
    "subtotal",
    "vat_amount",
    "total",
]
NUMBER_TOLERANCE = 0.01
ARABIC_DIACRITICS = re.compile(r"[ً-ْٰ]")


def normalize_text(value: str) -> str:
    value = ARABIC_DIACRITICS.sub("", normalize_digits(value))
    return " ".join(value.split()).casefold()


def same_text(a: str | None, b: str | None) -> bool:
    if a is None or b is None:
        return a is b
    return normalize_text(a) == normalize_text(b)


def same_number(a: float, b: float) -> bool:
    return abs(a - b) <= NUMBER_TOLERANCE


def same_item(a: LineItem, b: LineItem) -> bool:
    return (
        same_text(a.description, b.description)
        and same_number(a.quantity, b.quantity)
        and same_number(a.unit_price, b.unit_price)
        and same_number(a.line_total, b.line_total)
    )


def same_items(a: list[LineItem], b: list[LineItem]) -> bool:
    return len(a) == len(b) and all(same_item(x, y) for x, y in zip(a, b))


def score_invoice(expected: Invoice, actual: Invoice) -> dict[str, bool]:
    return {
        "supplier_name": same_text(expected.supplier_name, actual.supplier_name),
        "supplier_trn": same_text(expected.supplier_trn, actual.supplier_trn),
        "invoice_number": same_text(expected.invoice_number, actual.invoice_number),
        "invoice_date": expected.invoice_date == actual.invoice_date,
        "currency": same_text(expected.currency, actual.currency),
        "items": same_items(expected.items, actual.items),
        "subtotal": same_number(expected.subtotal, actual.subtotal),
        "vat_amount": same_number(expected.vat_amount, actual.vat_amount),
        "total": same_number(expected.total, actual.total),
    }
