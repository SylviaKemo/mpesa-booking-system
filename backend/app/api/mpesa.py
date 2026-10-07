import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path, status
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import get_db
from app.services.calendar import sync_in_background
from app.services.payments import handle_callback

logger = logging.getLogger(__name__)

router = APIRouter(tags=["mpesa"])


@router.post("/mpesa/callback/{secret}")
def mpesa_callback(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
    secret: str = Path(description="The shared secret from MPESA_CALLBACK_SECRET."),
    db: Session = Depends(get_db),
    settings: Settings = Depends(get_settings),
) -> dict[str, Any]:
    """
    Receive Safaricom's verdict on a prompt.

    Safaricom does not sign callbacks, so the URL carries an unguessable
    segment; without it anyone who found the endpoint could post a forged
    confirmation and take a slot without paying.

    Always answers 200 for anything it could parse, including a payment it does
    not recognise, because a non-200 makes Safaricom retry a request that will
    never succeed. Genuine processing failures are left to raise so the retry
    is useful.
    """
    if not settings.mpesa_callback_secret or secret != settings.mpesa_callback_secret:
        logger.warning("Rejected M-Pesa callback with a bad secret")
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")

    try:
        outcome = handle_callback(db, payload)
    except ValueError as exc:
        # Malformed and will stay malformed; retrying it helps nobody.
        logger.warning("Unparseable M-Pesa callback: %s", exc)
        return {"ResultCode": 0, "ResultDesc": "Accepted"}

    logger.info("M-Pesa callback: %s", outcome.detail)

    if outcome.confirmed:
        # After the reply, not before it: a slow Google must not hold
        # Safaricom's request open, and a calendar failure must not turn a
        # settled payment into a retried callback.
        background_tasks.add_task(sync_in_background)

    # Safaricom expects this envelope, and reads a non-zero code as "retry".
    return {"ResultCode": 0, "ResultDesc": "Accepted"}
