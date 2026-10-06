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
        _settings_from_env(monkeypatch, CORS_ORIGINS="*", ENVIRONMENT="production")


def test_is_sqlite_detects_driver() -> None:
    assert Settings(database_url="sqlite:///./x.db").is_sqlite is True
    assert Settings(database_url="postgresql+psycopg://u@h/db").is_sqlite is False
