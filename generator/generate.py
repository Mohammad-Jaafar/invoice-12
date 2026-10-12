from datetime import date
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from app.schema import Invoice, LineItem

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = Path(__file__).resolve().parent / "templates"
OUT_DIR = ROOT / "data" / "clean"


def build_invoice() -> Invoice:
    rows = [
        ("Office chair", 2, 450.00),
        ("Desk lamp", 3, 85.50),
        ("A4 paper box", 10, 22.75),
    ]
    items = [
        LineItem(description=d, quantity=q, unit_price=p, line_total=round(q * p, 2))
        for d, q, p in rows
    ]
    subtotal = round(sum(i.line_total for i in items), 2)
    vat_amount = round(subtotal * 0.05, 2)
    return Invoice(
        supplier_name="Gulf Office Supplies LLC",
        supplier_trn="100234567800003",
        invoice_number="INV-2026-0001",
        invoice_date=date(2026, 10, 11),
        currency="AED",
        items=items,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total=round(subtotal + vat_amount, 2),
    )


def render_html(invoice: Invoice) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    return env.get_template("classic.html").render(invoice=invoice)


def save_png(html: str, path: Path) -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 794, "height": 1123}, device_scale_factor=1.5
        )
        page.set_content(html)
        page.screenshot(path=path)
        browser.close()


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    invoice = build_invoice()
    png_path = OUT_DIR / "inv_000.png"
    save_png(render_html(invoice), png_path)
    png_path.with_suffix(".json").write_text(
        invoice.model_dump_json(indent=2), encoding="utf-8"
    )
    print(png_path)


if __name__ == "__main__":
    main()
