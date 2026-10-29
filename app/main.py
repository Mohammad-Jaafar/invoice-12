import hashlib
import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app import db
from app.db import get_session
from app.extractor import MEDIA_TYPES, MODEL, extract_bytes
from app.models import Extraction
from app.validator import validate

TAGS = {"demo", "real", "synthetic"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    yield


app = FastAPI(title="Invoice Extractor", lifespan=lifespan)


def summary(row: Extraction) -> dict:
    return {
        "id": row.id,
        "created_at": row.created_at.isoformat(),
        "filename": row.filename,
        "tag": row.tag,
        "model": row.model,
        "status": row.status,
        "problems": row.problems,
        "review_status": row.review_status,
    }


@app.get("/health")
def health(session: Session = Depends(get_session)):
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(status_code=503, content={"status": "error", "database": "unreachable"})
    return {"status": "ok", "database": "ok"}


@app.post("/extract")
def extract(file: UploadFile, tag: str = "demo", session: Session = Depends(get_session)) -> dict:
    if tag not in TAGS:
        raise HTTPException(status_code=400, detail="tag must be demo, real or synthetic")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Upload a PNG, JPG or WebP image")
    data = file.file.read()
    sha256 = hashlib.sha256(data).hexdigest()
    existing = session.scalar(select(Extraction).where(Extraction.sha256 == sha256))
    if existing:
        return {**summary(existing), "duplicate": True, "invoice": existing.data}
    media_type = MEDIA_TYPES[suffix]
    start = time.perf_counter()
    invoice, usage = extract_bytes(data, media_type)
    seconds = time.perf_counter() - start
    result = validate(invoice)
    row = Extraction(
        filename=file.filename,
        media_type=media_type,
        sha256=sha256,
        image=data,
        tag=tag,
        model=MODEL,
        status=result.status,
        problems=result.problems,
        data=invoice.model_dump(mode="json"),
        input_tokens=usage["input_tokens"] or 0,
        output_tokens=usage["output_tokens"] or 0,
        seconds=seconds,
    )
    session.add(row)
    session.commit()
    return {**summary(row), "duplicate": False, "invoice": row.data, "usage": usage}


@app.get("/extractions")
def list_extractions(
    limit: int = Query(20, ge=1, le=200), session: Session = Depends(get_session)
) -> list[dict]:
    rows = session.scalars(
        select(Extraction).order_by(Extraction.created_at.desc(), Extraction.id.desc()).limit(limit)
    ).all()
    return [summary(row) for row in rows]


@app.get("/extractions/{id}")
def get_extraction(id: int, session: Session = Depends(get_session)) -> dict:
    row = session.get(Extraction, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return {**summary(row), "invoice": row.data, "reviewed": row.reviewed_data}
