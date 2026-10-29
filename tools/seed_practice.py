import json
import os
from pathlib import Path
 
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
 
load_dotenv()
url = os.environ["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg://", 1)
engine = create_engine(url)
 
rows = []
for path in sorted(Path("data/clean").glob("*.json")):
    invoice = json.loads(path.read_text(encoding="utf-8"))
    rows.append(
        {
            "file": path.stem,
            "supplier": invoice["supplier_name"],
            "invoice_date": invoice["invoice_date"],
            "currency": invoice["currency"],
            "items": len(invoice["items"]),
            "subtotal": invoice["subtotal"],
            "vat": invoice["vat_amount"],
            "total": invoice["total"],
        }
    )
 
with engine.begin() as connection:
    connection.execute(text("DROP TABLE IF EXISTS practice"))
    connection.execute(
        text(
            "CREATE TABLE practice (id SERIAL PRIMARY KEY, file TEXT, supplier TEXT, invoice_date DATE, "
            "currency TEXT, items INT, subtotal NUMERIC(12,2), vat NUMERIC(12,2), total NUMERIC(12,2))"
        )
    )
    connection.execute(
        text(
            "INSERT INTO practice (file, supplier, invoice_date, currency, items, subtotal, vat, total) "
            "VALUES (:file, :supplier, :invoice_date, :currency, :items, :subtotal, :vat, :total)"
        ),
        rows,
    )
print(f"inserted {len(rows)} rows into practice")