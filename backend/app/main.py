from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import bookings, catalogue, health, mpesa
from app.config import get_settings


def create_app() -> FastAPI:
    """
    Build the application.

    Note this reads the process-wide cached settings; it does not isolate
    configuration per call. Overriding settings means clearing that cache
    (``get_settings.cache_clear()``) before importing ``app.database``, which
    binds its engine at import time.
    """
    settings = get_settings()

    app = FastAPI(
        title="Shamim Styles API",
        description="Bookings and M-Pesa payments for Shamim Styles.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        # False when origins are a wildcard — see Settings.allow_credentials.
        allow_credentials=settings.allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(catalogue.router, prefix="/api")
    app.include_router(bookings.router, prefix="/api")
    app.include_router(mpesa.router, prefix="/api")

    return app


app = create_app()
