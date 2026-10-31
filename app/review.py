from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, select
from sqlalchemy.orm import Session, defer

from app.db import get_session
from app.models import Extraction
from app.security import require_admin

router = APIRouter(prefix="/review", dependencies=[Depends(require_admin)])
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


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
