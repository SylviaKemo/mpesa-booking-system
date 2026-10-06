from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import health
from app.config import get_settings


def create_app() -> FastAPI:
    """App factory — lets tests build an app with overridden settings."""
    settings = get_settings()

    app = FastAPI(
        title="Shamim Styles API",
        description="Bookings and M-Pesa payments for Shamim Styles.",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")

    return app


app = create_app()
