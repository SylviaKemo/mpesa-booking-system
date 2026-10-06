from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict[str, str]:
    """
    Liveness plus a real database round-trip, so a deploy that cannot reach its
    database fails this check rather than reporting healthy.
    """
    db.execute(text("SELECT 1"))
    return {"status": "ok", "database": "ok"}
