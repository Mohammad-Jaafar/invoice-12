from datetime import date

from fastapi.testclient import TestClient

from app import main
from app.schema import Invoice, LineItem

client = TestClient(main.app)


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
        ],
        subtotal=100.0,
        vat_amount=5.0,
        total=105.0,
    )


def fake_extract_bytes(data: bytes, media_type: str) -> tuple[Invoice, dict]:
    return make_invoice(), {"input_tokens": 1000, "output_tokens": 200}


def test_health_returns_200():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_text_upload_returns_400():
    response = client.post(
        "/extract", files={"file": ("note.txt", b"hello", "text/plain")}
    )
    assert response.status_code == 400


def test_image_upload_returns_result(monkeypatch):
    monkeypatch.setattr(main, "extract_bytes", fake_extract_bytes)
    response = client.post(
        "/extract", files={"file": ("invoice.png", b"fake image", "image/png")}
    )
    assert response.status_code == 200
    assert set(response.json()) == {"status", "problems", "invoice", "usage"}
