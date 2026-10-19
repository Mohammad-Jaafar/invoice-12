from datetime import date

from app.schema import Invoice, LineItem
from app.validator import validate


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


def assert_one_problem(invoice: Invoice) -> None:
    result = validate(invoice)
    assert result.status == "needs_review"
    assert len(result.problems) == 1


def test_correct_invoice_is_ok():
    result = validate(make_invoice())
    assert result.status == "ok"
    assert result.problems == []


def test_rule1_quantity_times_price_must_equal_line_total():
    invoice = make_invoice()
    assert validate(invoice).status == "ok"
    invoice.items[0].quantity = 3
    assert_one_problem(invoice)


def test_rule2_sum_of_line_totals_must_equal_subtotal():
    invoice = make_invoice()
    assert validate(invoice).status == "ok"
    invoice.items[0].unit_price = 60.0
    invoice.items[0].line_total = 120.0
    assert_one_problem(invoice)


def test_rule3_vat_must_be_five_percent_of_subtotal():
    invoice = make_invoice()
    assert validate(invoice).status == "ok"
    invoice.vat_amount = 7.0
    invoice.total = 127.0
    assert_one_problem(invoice)


def test_rule4_subtotal_plus_vat_must_equal_total():
    invoice = make_invoice()
    assert validate(invoice).status == "ok"
    invoice.total = 130.0
    assert_one_problem(invoice)


def test_rule5_trn_must_be_15_digits():
    invoice = make_invoice()
    assert validate(invoice).status == "ok"
    invoice.supplier_trn = "12345"
    assert_one_problem(invoice)


def test_arabic_indic_trn_is_accepted():
    invoice = make_invoice()
    invoice.supplier_trn = "١" + "٠" * 13 + "٣"
    result = validate(invoice)
    assert result.status == "ok"
    assert result.problems == []
