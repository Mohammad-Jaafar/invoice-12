from datetime import date

from pydantic import BaseModel


class LineItem(BaseModel):
    description: str
    quantity: float
    unit_price: float
    line_total: float


class Invoice(BaseModel):
    supplier_name: str
    supplier_trn: str | None
    invoice_number: str
    invoice_date: date
    currency: str
    items: list[LineItem]
    subtotal: float
    vat_amount: float
    total: float
