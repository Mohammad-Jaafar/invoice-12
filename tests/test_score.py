from datetime import date

import pytest

from app.schema import Invoice, LineItem
from eval.score import FIELDS, score_invoice


def make_invoice() -> Invoice:
    return Invoice(
        supplier_name="Test Supplier LLC",
        supplier_trn="100000000000003",
        invoice_number="INV-2026-0001",
        invoice_date=date(2026, 1, 15),
        currency="AED",
        items=[
            LineItem(
                description="Desk lamp", quantity=2, unit_price=50.0, line_total=100.0
            ),
            LineItem(
                description="Paper box", quantity=1, unit_price=20.0, line_total=20.0
            ),
        ],
        subtotal=120.0,
        vat_amount=6.0,
        total=126.0,
    )


CHANGES = {
    "supplier_name": "Other Supplier LLC",
    "supplier_trn": "100000000000009",
    "invoice_number": "INV-2026-0002",
    "invoice_date": date(2026, 1, 16),
    "currency": "SAR",
    "items": [
        LineItem(
            description="Office chair", quantity=2, unit_price=50.0, line_total=100.0
        ),
        LineItem(description="Paper box", quantity=1, unit_price=20.0, line_total=20.0),
    ],
    "subtotal": 121.0,
    "vat_amount": 7.0,
    "total": 127.0,
}


def test_identical_invoices_all_true():
    result = score_invoice(make_invoice(), make_invoice())
    assert list(result) == FIELDS
    assert all(result.values())


@pytest.mark.parametrize("field", FIELDS)
def test_changing_one_field_makes_only_that_field_false(field):
    actual = make_invoice()
    setattr(actual, field, CHANGES[field])
    result = score_invoice(make_invoice(), actual)
    assert result[field] is False
    assert all(value for name, value in result.items() if name != field)


def test_case_spaces_and_arabic_indic_digits_still_match():
    actual = make_invoice()
    actual.supplier_name = "  test   SUPPLIER llc "
    actual.supplier_trn = "١" + "٠" * 13 + "٣"
    actual.invoice_number = "inv-٢٠٢٦-٠٠٠١"
    actual.items[0].description = "DESK  lamp"
    result = score_invoice(make_invoice(), actual)
    assert all(result.values())
