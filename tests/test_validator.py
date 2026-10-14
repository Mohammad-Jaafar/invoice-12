from datetime import date

from app.schema import Invoice, LineItem
from app.validator import validate


def make_invoice(first_line_total: float) -> Invoice:
    return Invoice(
        supplier_name="Test Supplier LLC",
        supplier_trn="100000000000003",
        invoice_number="INV-2026-0001",
        invoice_date=date(2026, 1, 15),
        currency="AED",
        items=[
            LineItem(
                description="Desk lamp",
                quantity=2,
                unit_price=50.0,
                line_total=first_line_total,
            ),
            LineItem(
                description="Paper box", quantity=1, unit_price=20.0, line_total=20.0
            ),
        ],
        subtotal=120.0,
        vat_amount=6.0,
        total=126.0,
    )


def test_correct_invoice_is_ok():
    result = validate(make_invoice(100.0))
    assert result.status == "ok"
    assert result.problems == []


def test_wrong_line_total_needs_review():
    result = validate(make_invoice(150.0))
    assert result.status == "needs_review"
    assert len(result.problems) == 1
