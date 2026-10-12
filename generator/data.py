import random
from datetime import date, timedelta

from app.schema import Invoice, LineItem

SUPPLIERS = [
    ("Gulf Office Supplies LLC", "الخليج للوازم المكتبية ذ.م.م"),
    ("Al Noor Trading Co.", "شركة النور التجارية"),
    ("Emirates Tech Solutions", "الإمارات للحلول التقنية"),
    ("Desert Rose Catering", "وردة الصحراء للتموين"),
    ("Blue Wave Logistics", "الموجة الزرقاء للخدمات اللوجستية"),
    ("Al Falah Building Materials", "الفلاح لمواد البناء"),
    ("Oasis Cleaning Services", "الواحة لخدمات التنظيف"),
    ("Palm City Electronics", "مدينة النخيل للإلكترونيات"),
    ("Crescent Printing Press", "مطبعة الهلال"),
    ("Sharjah Medical Supplies", "الشارقة للمستلزمات الطبية"),
]

SUPPLIER_AR = dict(SUPPLIERS)

PRODUCTS = [
    ("Office chair", "كرسي مكتب", 250, 900),
    ("Desk lamp", "مصباح مكتب", 40, 180),
    ("A4 paper box", "علبة ورق A4", 18, 35),
    ("Printer toner", "حبر طابعة", 120, 450),
    ("Laptop", "حاسوب محمول", 2200, 6500),
    ("Wireless mouse", "فأرة لاسلكية", 35, 120),
    ("Monitor 27 inch", "شاشة 27 بوصة", 650, 1800),
    ("Network cable 5m", "كابل شبكة 5 م", 15, 45),
    ("Cleaning service", "خدمة تنظيف", 300, 1500),
    ("IT support hour", "ساعة دعم فني", 150, 400),
    ("Delivery fee", "رسوم توصيل", 25, 150),
    ("Catering package", "باقة ضيافة", 500, 3000),
    ("Water dispenser", "موزع مياه", 350, 950),
    ("Filing cabinet", "خزانة ملفات", 400, 1400),
    ("Business cards box", "علبة بطاقات عمل", 60, 220),
    ("Annual maintenance", "صيانة سنوية", 1200, 5000),
]


def pick_name(rng: random.Random, language: str, en: str, ar: str) -> str:
    if language == "en":
        return en
    if language == "ar":
        return ar
    return rng.choice([en, ar])


def build_invoice(rng: random.Random, language: str) -> Invoice:
    supplier_en, supplier_ar = rng.choice(SUPPLIERS)
    items = []
    for en, ar, low, high in rng.sample(PRODUCTS, rng.randint(2, 5)):
        quantity = rng.randint(1, 10)
        unit_price = round(rng.uniform(low, high), 2)
        items.append(
            LineItem(
                description=pick_name(rng, language, en, ar),
                quantity=quantity,
                unit_price=unit_price,
                line_total=round(quantity * unit_price, 2),
            )
        )
    subtotal = round(sum(item.line_total for item in items), 2)
    vat_amount = round(subtotal * 0.05, 2)
    return Invoice(
        supplier_name=supplier_ar if language == "ar" else supplier_en,
        supplier_trn=f"100{rng.randrange(10**12):012d}",
        invoice_number=f"INV-2026-{rng.randint(1, 9999):04d}",
        invoice_date=date(2026, 1, 1) + timedelta(days=rng.randrange(365)),
        currency="AED",
        items=items,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total=round(subtotal + vat_amount, 2),
    )
