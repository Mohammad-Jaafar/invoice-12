import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, select
from sqlalchemy.orm import Session, defer

from app.db import get_session
from app.models import Extraction
from app.security import require_admin

router = APIRouter(prefix="/review", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


def get_row(session: Session, id: int) -> Extraction:
    row = session.get(Extraction, id)
    if row is None:
        raise HTTPException(status_code=404, detail="Extraction not found")
    return row


@router.get("")
def review_list(request: Request, show: str = "pending", session: Session = Depends(get_session)):
    query = select(Extraction).options(defer(Extraction.image))
    if show == "pending":
        query = query.where(Extraction.review_status == "pending")
    query = query.order_by(
        case((Extraction.status == "needs_review", 0), else_=1), Extraction.id.desc()
    ).limit(200)
    rows = session.scalars(query).all()
    return templates.TemplateResponse(request, "list.html", {"rows": rows, "show": show})


@router.get("/{id}/image")
def review_image(id: int, session: Session = Depends(get_session)):
    row = get_row(session, id)
    return Response(content=row.image, media_type=row.media_type)


@router.get("/{id}")
def review_detail(request: Request, id: int, session: Session = Depends(get_session)):
    row = get_row(session, id)
    invoice = row.reviewed_data or row.data
    invoice_json = json.dumps(invoice, ensure_ascii=False, indent=2)
    return templates.TemplateResponse(
        request,
        "detail.html",
        {"row": row, "invoice": invoice, "invoice_json": invoice_json, "error": None},
    )
