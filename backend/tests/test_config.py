import json

import pytest
from pydantic import ValidationError

from app.config import Settings


def _settings_from_env(monkeypatch: pytest.MonkeyPatch, **env: str) -> Settings:
    """
    Build Settings the way the application does — through the environment.

    Passing values as init kwargs would bypass pydantic-settings' env source
    entirely, which is where the decoding happens, so these tests would pass
    against configuration the real app cannot load.
    """
    for key, value in env.items():
        monkeypatch.setenv(key, value)
    return Settings()


_SERVICE_ACCOUNT = json.dumps(
    {"client_email": "booking@shamim.iam.gserviceaccount.com", "private_key": "pem"}
)


def _production() -> dict[str, str]:
    """A production config that satisfies every guard."""
    return {
        "ENVIRONMENT": "production",
        "MPESA_PROVIDER": "daraja",
        "MPESA_CALLBACK_SECRET": "s3cret",
        "MPESA_CONSUMER_KEY": "key",
        "MPESA_CONSUMER_SECRET": "secret",
        "MPESA_CALLBACK_BASE_URL": "https://shamimstyles.co.ke",
        "CALENDAR_PROVIDER": "google",
        "GOOGLE_CALENDAR_ID": "shamim@gmail.com",
        "GOOGLE_SERVICE_ACCOUNT_JSON": _SERVICE_ACCOUNT,
    }


def test_single_origin_loads_from_the_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The exact value shipped in .env.example must load."""
    settings = _settings_from_env(monkeypatch, CORS_ORIGINS="http://localhost:3000")

    assert settings.cors_origins == ["http://localhost:3000"]


def test_cors_origins_parse_from_comma_separated_string(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    settings = _settings_from_env(
        monkeypatch, CORS_ORIGINS="http://a.test, http://b.test"
    )

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_ignore_blank_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings_from_env(
        monkeypatch, CORS_ORIGINS="http://a.test,,  ,http://b.test"
    )

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_wildcard_origin_disables_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    """Echoing any origin back with credentials would open the API to any site."""
    settings = _settings_from_env(
        monkeypatch, CORS_ORIGINS="*", ENVIRONMENT="development"
    )

    assert settings.allow_credentials is False


def test_named_origins_keep_credentials(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = _settings_from_env(monkeypatch, CORS_ORIGINS="http://a.test")

    assert settings.allow_credentials is True


def test_wildcard_origin_is_refused_in_production(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with pytest.raises(ValidationError, match="CORS_ORIGINS"):
        # The rest of the production config is supplied so this reaches the
        # CORS check rather than tripping an earlier guard.
        _settings_from_env(
            monkeypatch,
            CORS_ORIGINS="*",
            **_production(),
        )


def test_production_refuses_the_fake_payment_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A deployment that silently takes no payments is worse than one that will not start."""
    with pytest.raises(ValidationError, match="MPESA_PROVIDER"):
        _settings_from_env(
            monkeypatch,
            CORS_ORIGINS="https://shamimstyles.co.ke",
            **{**_production(), "MPESA_PROVIDER": "fake"},
        )


def test_production_requires_a_callback_secret(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Without it the callback URL is guessable and anyone could forge a confirmation."""
    # conftest sets a secret for the whole session; this case needs it absent.
    monkeypatch.delenv("MPESA_CALLBACK_SECRET", raising=False)
    config = _production()
    config.pop("MPESA_CALLBACK_SECRET")

    with pytest.raises(ValidationError, match="MPESA_CALLBACK_SECRET"):
        _settings_from_env(
            monkeypatch, CORS_ORIGINS="https://shamimstyles.co.ke", **config
        )


def test_a_full_production_config_loads(monkeypatch: pytest.MonkeyPatch) -> None:
    """The guards below each fail one value; this proves the baseline passes."""
    settings = _settings_from_env(
        monkeypatch, CORS_ORIGINS="https://shamimstyles.co.ke", **_production()
    )

    assert settings.calendar_provider == "google"


def test_production_refuses_the_fake_calendar(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The calendar is Shamim's only view of bookings; without it she would miss clients."""
    with pytest.raises(ValidationError, match="CALENDAR_PROVIDER"):
        _settings_from_env(
            monkeypatch,
            CORS_ORIGINS="https://shamimstyles.co.ke",
            **{**_production(), "CALENDAR_PROVIDER": "fake"},
        )


@pytest.mark.parametrize("missing", ["GOOGLE_CALENDAR_ID", "GOOGLE_SERVICE_ACCOUNT_JSON"])
def test_the_google_calendar_needs_its_id_and_key(
    monkeypatch: pytest.MonkeyPatch, missing: str
) -> None:
    config = {
        "CALENDAR_PROVIDER": "google",
        "GOOGLE_CALENDAR_ID": "shamim@gmail.com",
        "GOOGLE_SERVICE_ACCOUNT_JSON": _SERVICE_ACCOUNT,
    }
    config.pop(missing)

    with pytest.raises(ValidationError, match=missing):
        _settings_from_env(monkeypatch, **config)


@pytest.mark.parametrize(
    "key",
    [
        "not json",
        json.dumps({"client_email": "booking@shamim.iam.gserviceaccount.com"}),
        json.dumps(["a", "list"]),
    ],
)
def test_a_malformed_service_account_key_is_refused_at_startup(
    monkeypatch: pytest.MonkeyPatch, key: str
) -> None:
    """Caught here rather than on the first paid booking, which would never reach the calendar."""
    with pytest.raises(ValidationError, match="GOOGLE_SERVICE_ACCOUNT_JSON"):
        _settings_from_env(
            monkeypatch,
            CALENDAR_PROVIDER="google",
            GOOGLE_CALENDAR_ID="shamim@gmail.com",
            GOOGLE_SERVICE_ACCOUNT_JSON=key,
        )


def test_is_sqlite_detects_driver() -> None:
    assert Settings(database_url="sqlite:///./x.db").is_sqlite is True
    assert Settings(database_url="postgresql+psycopg://u@h/db").is_sqlite is False


def test_settings_do_not_read_a_developers_env_file_under_test() -> None:
    """
    The suite used to load backend/.env, so a local MPESA_PROVIDER=daraja made
    tests fire live Safaricom requests, and a populated file masked the cases
    asserting a value is absent. conftest disables it; this notices if that
    stops working.
    """
    assert Settings.model_config.get("env_file") is None
