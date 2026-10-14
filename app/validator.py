from pydantic import BaseModel

from app.schema import Invoice

TOLERANCE = 0.02


class ValidationResult(BaseModel):
    status: str
    problems: list[str]


def validate(invoice: Invoice) -> ValidationResult:
    problems = []
    items_total = sum(item.line_total for item in invoice.items)
    if abs(items_total - invoice.subtotal) > TOLERANCE:
        problems.append(
            f"sum of line totals {items_total:.2f} != subtotal {invoice.subtotal:.2f}"
        )
    status = "needs_review" if problems else "ok"
    return ValidationResult(status=status, problems=problems)
