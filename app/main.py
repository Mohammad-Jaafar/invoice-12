from pathlib import Path

from fastapi import FastAPI, HTTPException, UploadFile

from app.extractor import MEDIA_TYPES, extract_bytes
from app.validator import validate

app = FastAPI(title="Invoice Extractor")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/extract")
def extract(file: UploadFile) -> dict:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PNG, JPG or WebP image")
    invoice, usage = extract_bytes(file.file.read(), MEDIA_TYPES[suffix])
    result = validate(invoice)
    return {
        "status": result.status,
        "problems": result.problems,
        "invoice": invoice.model_dump(mode="json"),
        "usage": usage,
    }
