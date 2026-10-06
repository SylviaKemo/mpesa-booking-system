from app.config import Settings


def test_cors_origins_parse_from_comma_separated_string() -> None:
    """The environment can only carry strings, so the list has to be parsed."""
    settings = Settings(cors_origins="http://a.test, http://b.test")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_cors_origins_ignore_blank_entries() -> None:
    settings = Settings(cors_origins="http://a.test,,  ,http://b.test")

    assert settings.cors_origins == ["http://a.test", "http://b.test"]


def test_is_sqlite_detects_driver() -> None:
    assert Settings(database_url="sqlite:///./x.db").is_sqlite is True
    assert Settings(database_url="postgresql+psycopg://u@h/db").is_sqlite is False
