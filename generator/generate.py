import argparse
import random
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from app.schema import Invoice
from generator.data import SUPPLIER_AR, build_invoice

TEMPLATES = Path(__file__).resolve().parent / "templates"
LANGUAGES = ["en", "ar", "mixed"]
ARABIC_DIGITS = str.maketrans("0123456789", "٠١٢٣٤٥٦٧٨٩")
EN_LABELS = {
    "title": "TAX INVOICE",
    "trn": "TRN",
    "invoice_number": "Invoice No",
    "date": "Date",
    "description": "Description",
    "quantity": "Qty",
    "unit_price": "Unit Price",
    "amount": "Amount",
    "subtotal": "Subtotal",
    "vat": "VAT 5%",
    "total": "Total",
}
AR_LABELS = {
    "title": "فاتورة ضريبية",
    "trn": "الرقم الضريبي",
    "invoice_number": "رقم الفاتورة",
    "date": "التاريخ",
    "description": "الوصف",
    "quantity": "الكمية",
    "unit_price": "سعر الوحدة",
    "amount": "الإجمالي",
    "subtotal": "المجموع الفرعي",
    "vat": "ضريبة القيمة المضافة 5%",
    "total": "الإجمالي المستحق",
}
LABELS = {
    "en": EN_LABELS,
    "ar": AR_LABELS,
    "mixed": {key: f"{AR_LABELS[key]} / {EN_LABELS[key]}" for key in EN_LABELS},
}


def supplier_names(invoice: Invoice, language: str) -> list[str]:
    if language == "mixed":
        return [SUPPLIER_AR[invoice.supplier_name], invoice.supplier_name]
    return [invoice.supplier_name]


def render_html(
    invoice: Invoice, language: str, layout: str, arabic_digits: bool
) -> str:
    env = Environment(loader=FileSystemLoader(TEMPLATES), autoescape=True)
    env.filters["digits"] = (
        lambda value: str(value).translate(ARABIC_DIGITS) if arabic_digits else value
    )
    return env.get_template(f"{layout}.html").render(
        invoice=invoice,
        labels=LABELS[language],
        supplier_names=supplier_names(invoice, language),
        lang="en" if language == "en" else "ar",
        direction="ltr" if language == "en" else "rtl",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=10)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=Path("data/clean"))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    rng = random.Random(args.seed)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 794, "height": 1123}, device_scale_factor=1.5
        )
        for i in range(args.count):
            language = LANGUAGES[i % 3]
            layout = "classic" if i % 6 < 3 else "modern"
            invoice = build_invoice(rng, language)
            arabic_digits = language != "en" and rng.random() < 0.5
            stem = f"inv_{i:03d}_{language}_{layout}"
            page.set_content(render_html(invoice, language, layout, arabic_digits))
            page.screenshot(path=args.out / f"{stem}.png")
            (args.out / f"{stem}.json").write_text(
                invoice.model_dump_json(indent=2), encoding="utf-8"
            )
            print(stem)
        browser.close()


if __name__ == "__main__":
    main()
