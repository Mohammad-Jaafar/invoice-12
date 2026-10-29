import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import Base, engine
from app.main import app
from app.schema import Invoice

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"


class FakeExtractor:
    def __init__(self):
        self.calls = 0
        self.truth = {path.read_bytes(): path.with_suffix(".json") for path in CLEAN.glob("*.png")}

    def __call__(self, data: bytes, media_type: str) -> tuple[Invoice, dict]:
        self.calls += 1
        invoice = Invoice.model_validate_json(self.truth[data].read_text(encoding="utf-8"))
        return invoice, {"input_tokens": 1000, "output_tokens": 200}


@pytest.fixture(autouse=True)
def fake(monkeypatch):
    Base.metadata.drop_all(engine)
    extractor = FakeExtractor()
    monkeypatch.setattr(main, "extract_bytes", extractor)
    return extractor


def upload(client: TestClient, name: str, tag: str = "demo"):
    path = CLEAN / name
    return client.post(
        "/extract", params={"tag": tag}, files={"file": (path.name, path.read_bytes(), "image/png")}
    )


def truth(name: str) -> dict:
    return json.loads((CLEAN / name).with_suffix(".json").read_text(encoding="utf-8"))


def test_health_reports_database_ok():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_upload_returns_new_row():
    with TestClient(app) as client:
        response = upload(client, "inv_000_en_classic.png")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["duplicate"] is False


def test_same_image_is_a_duplicate(fake):
    with TestClient(app) as client:
        first = upload(client, "inv_000_en_classic.png").json()
        second = upload(client, "inv_000_en_classic.png").json()
    assert second["id"] == first["id"]
    assert second["duplicate"] is True
    assert fake.calls == 1


def test_bad_file_and_bad_tag_return_400():
    with TestClient(app) as client:
        text_file = client.post("/extract", files={"file": ("note.txt", b"hello", "text/plain")})
        bad_tag = upload(client, "inv_000_en_classic.png", tag="other")
    assert text_file.status_code == 400
    assert bad_tag.status_code == 400


def test_list_and_detail():
    with TestClient(app) as client:
        created = upload(client, "inv_000_en_classic.png").json()
        listed = client.get("/extractions").json()
        detail = client.get(f"/extractions/{created['id']}")
        missing = client.get("/extractions/999999")
    assert listed[0]["id"] == created["id"]
    assert "image" not in listed[0]
    assert detail.status_code == 200
    assert detail.json()["invoice"]["invoice_number"] == truth("inv_000_en_classic.png")["invoice_number"]
    assert detail.json()["invoice"]["total"] == truth("inv_000_en_classic.png")["total"]
    assert missing.status_code == 404


def test_arabic_supplier_name_survives_round_trip():
    with TestClient(app) as client:
        created = upload(client, "inv_001_ar_classic.png").json()
        detail = client.get(f"/extractions/{created['id']}").json()
    assert detail["invoice"]["supplier_name"] == truth("inv_001_ar_classic.png")["supplier_name"]
