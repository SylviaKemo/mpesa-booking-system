from functools import lru_cache
from typing import Annotated, Literal
from zoneinfo import ZoneInfo, available_timezones

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """
    Configuration read from the environment, with a .env file as a fallback.

    Every value has a development-safe default so the app starts on a fresh
    checkout, but nothing secret is ever defaulted — secrets arrive from the
    environment only. See .env.example for the full list.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    environment: Literal["development", "production"] = "development"

    # SQLite by default; a postgresql+psycopg:// URL works unchanged.
    database_url: str = "sqlite:///./shamim.db"

    # The salon's wall clock. A deployment running UTC would otherwise disagree
    # with Nairobi for three hours every night, and treat a day that has already
    # finished locally as still bookable.
    salon_timezone: str = "Africa/Nairobi"

    # How far ahead a booking may be made. Mirrors what the calendar offers, and
    # stops a slot being held years out where nobody would ever see it.
    max_booking_lead_days: int = 180

    # NoDecode stops pydantic-settings JSON-decoding the raw environment value.
    # Without it a bare "http://localhost:3000" is handed to json.loads() and
    # raises before the validator below runs, so every CORS_ORIGINS value fails.
    cors_origins: Annotated[list[str], NoDecode] = ["http://localhost:3000"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, value: object) -> object:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @model_validator(mode="after")
    def _refuse_wildcard_origin_in_production(self) -> "Settings":
        """
        A wildcard origin is never acceptable in production: paired with
        credentialed CORS it lets any site call the API on a user's behalf.
        Fail loudly at startup rather than serving a permissive policy.
        """
        if self.environment == "production" and "*" in self.cors_origins:
            raise ValueError(
                'CORS_ORIGINS cannot be "*" when ENVIRONMENT=production. '
                "List the exact origins allowed to call the API."
            )
        return self

    @field_validator("salon_timezone")
    @classmethod
    def _known_timezone(cls, value: str) -> str:
        if value not in available_timezones():
            raise ValueError(f"Unknown timezone: {value!r}")
        return value

    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.salon_timezone)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def allow_credentials(self) -> bool:
        """
        Credentials and a wildcard origin are mutually exclusive — together they
        make Starlette echo any caller's origin back with
        access-control-allow-credentials: true. In development, where a wildcard
        is permitted, drop credentials rather than widen access.
        """
        return "*" not in self.cors_origins


@lru_cache
def get_settings() -> Settings:
    """Cached so the environment is read once per process."""
    return Settings()
