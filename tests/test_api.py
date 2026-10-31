import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app import main
from app.db import Base, engine
from app.main import app
from app.schema import Invoice

CLEAN = Path(__file__).resolve().parent.parent / "data" / "clean"
AUTH = ("admin", "secret")
TOKEN = "token123"
API_HEADERS = {"X-API-Key": TOKEN}
FIRST = "inv_000_en_classic.png"
SECOND = "inv_001_ar_classic.png"


class FakeExtractor:
    def __init__(self):
        self.calls = 0
        self.truth = {path.read_bytes(): path.with_suffix(".json") for path in CLEAN.glob("*.png")}

    def __call__(self, data: bytes, media_type: str) -> tuple[Invoice, dict]:
        self.calls += 1
        invoice = Invoice.model_validate_json(self.truth[data].read_text(encoding="utf-8"))
        if self.calls == 2:
            invoice.total = round(invoice.total + 10, 2)
        return invoice, {"input_tokens": 1000, "output_tokens": 200}


@pytest.fixture(autouse=True)
def fake(monkeypatch):
    Base.metadata.drop_all(engine)
    extractor = FakeExtractor()
    monkeypatch.setattr(main, "extract_bytes", extractor)
    return extractor


@pytest.fixture(autouse=True)
def admin(monkeypatch):
    monkeypatch.setenv("ADMIN_USER", AUTH[0])
    monkeypatch.setenv("ADMIN_PASSWORD", AUTH[1])
    monkeypatch.setenv("API_TOKEN", TOKEN)


def upload(client: TestClient, name: str, tag: str = "demo", headers: dict | None = None):
    path = CLEAN / name
    return client.post(
        "/extract",
        params={"tag": tag},
        files={"file": (path.name, path.read_bytes(), "image/png")},
        headers=API_HEADERS if headers is None else headers,
    )


def truth(name: str) -> dict:
    return json.loads((CLEAN / name).with_suffix(".json").read_text(encoding="utf-8"))


def upload_two(client: TestClient) -> tuple[dict, dict]:
    return upload(client, FIRST).json(), upload(client, SECOND).json()


def test_health_reports_database_ok():
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_upload_returns_new_row():
    with TestClient(app) as client:
        response = upload(client, FIRST)
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body["id"], int)
    assert body["duplicate"] is False


def test_same_image_is_a_duplicate(fake):
    with TestClient(app) as client:
        first = upload(client, FIRST).json()
        second = upload(client, FIRST).json()
    assert second["id"] == first["id"]
    assert second["duplicate"] is True
    assert fake.calls == 1


def test_bad_file_and_bad_tag_return_400():
    with TestClient(app) as client:
        text_file = client.post(
            "/extract",
            files={"file": ("note.txt", b"hello", "text/plain")},
            headers=API_HEADERS,
        )
        bad_tag = upload(client, FIRST, tag="other")
    assert text_file.status_code == 400
    assert bad_tag.status_code == 400


def test_list_and_detail():
    with TestClient(app) as client:
        created = upload(client, FIRST).json()
        listed = client.get("/extractions", auth=AUTH).json()
        detail = client.get(f"/extractions/{created['id']}", auth=AUTH)
        missing = client.get("/extractions/999999", auth=AUTH)
    assert listed[0]["id"] == created["id"]
    assert "image" not in listed[0]
    assert detail.status_code == 200
    assert detail.json()["invoice"]["invoice_number"] == truth(FIRST)["invoice_number"]
    assert detail.json()["invoice"]["total"] == truth(FIRST)["total"]
    assert missing.status_code == 404


def test_arabic_supplier_name_survives_round_trip():
    with TestClient(app) as client:
        created = upload(client, SECOND).json()
        detail = client.get(f"/extractions/{created['id']}", auth=AUTH).json()
    assert detail["invoice"]["supplier_name"] == truth(SECOND)["supplier_name"]


def test_review_requires_correct_credentials():
    with TestClient(app) as client:
        anonymous = client.get("/review")
        wrong = client.get("/review", auth=("admin", "wrong"))
        right = client.get("/review", auth=AUTH)
    assert anonymous.status_code == 401
    assert wrong.status_code == 401
    assert right.status_code == 200


def test_extractions_requires_login():
    with TestClient(app) as client:
        response = client.get("/extractions")
    assert response.status_code == 401


def test_review_detail_page_and_image():
    with TestClient(app) as client:
        first, second = upload_two(client)
        pages = [client.get(f"/review/{row['id']}", auth=AUTH) for row in (first, second)]
        image = client.get(f"/review/{first['id']}/image", auth=AUTH)
    for page in pages:
        assert page.status_code == 200
        assert "<img" in page.text
        assert "<textarea" in page.text
    assert image.status_code == 200
    assert image.content == (CLEAN / FIRST).read_bytes()
    assert image.headers["content-type"].startswith("image/")


def test_save_corrections_marks_wrong_invoice_as_corrected():
    with TestClient(app) as client:
        first, second = upload_two(client)
        response = client.post(
            f"/review/{second['id']}",
            data={"action": "save", "invoice_json": json.dumps(truth(SECOND), ensure_ascii=False)},
            auth=AUTH,
            follow_redirects=False,
        )
        detail = client.get(f"/extractions/{second['id']}", auth=AUTH).json()
    assert response.status_code == 303
    assert detail["review_status"] == "corrected"
    assert detail["reviewed"]["total"] == truth(SECOND)["total"]
    assert detail["invoice"]["total"] == pytest.approx(truth(SECOND)["total"] + 10)


def test_approve_marks_invoice_as_approved():
    with TestClient(app) as client:
        first, second = upload_two(client)
        response = client.post(
            f"/review/{first['id']}",
            data={"action": "approve"},
            auth=AUTH,
            follow_redirects=False,
        )
        detail = client.get(f"/extractions/{first['id']}", auth=AUTH).json()
    assert response.status_code == 303
    assert detail["review_status"] == "approved"


def test_broken_json_returns_422():
    with TestClient(app) as client:
        first, second = upload_two(client)
        response = client.post(
            f"/review/{first['id']}",
            data={"action": "save", "invoice_json": "{broken"},
            auth=AUTH,
            follow_redirects=False,
        )
        detail = client.get(f"/extractions/{first['id']}", auth=AUTH).json()
    assert response.status_code == 422
    assert detail["review_status"] == "pending"


def test_stats_page_loads():
    with TestClient(app) as client:
        upload_two(client)
        response = client.get("/review/stats", auth=AUTH)
    assert response.status_code == 200


def test_extract_without_api_key_returns_401():
    with TestClient(app) as client:
        response = upload(client, FIRST, headers={})
    assert response.status_code == 401


def test_extract_with_wrong_api_key_returns_401():
    with TestClient(app) as client:
        response = upload(client, FIRST, headers={"X-API-Key": "wrong"})
    assert response.status_code == 401


def test_large_upload_returns_413(monkeypatch):
    monkeypatch.setenv("MAX_UPLOAD_MB", "1")
    big = b"x" * (2 * 1024 * 1024)
    with TestClient(app) as client:
        response = client.post(
            "/extract", files={"file": ("big.png", big, "image/png")}, headers=API_HEADERS
        )
    assert response.status_code == 413


def test_daily_limit_blocks_new_images_but_not_duplicates(monkeypatch):
    monkeypatch.setenv("MAX_EXTRACTIONS_PER_DAY", "3")
    names = [path.name for path in sorted(CLEAN.glob("*.png"))[:4]]
    with TestClient(app) as client:
        codes = [upload(client, name).status_code for name in names]
        again = upload(client, names[0])
    assert codes == [200, 200, 200, 429]
    assert again.status_code == 200
    assert again.json()["duplicate"] is True
