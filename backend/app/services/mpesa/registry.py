"""Picks the provider the app runs with."""

from functools import lru_cache

from app.config import get_settings
from app.services.mpesa.base import MpesaProvider
from app.services.mpesa.daraja import DarajaProvider
from app.services.mpesa.fake import fake_provider


@lru_cache
def _daraja() -> DarajaProvider:
    """Built once: it caches an access token, which a fresh instance would lose."""
    return DarajaProvider(get_settings())


def get_provider() -> MpesaProvider:
    """
    The provider for the current configuration.

    Production cannot select the fake — Settings refuses to start on it — so
    this choice is only ever real in a deployment.
    """
    if get_settings().mpesa_provider == "daraja":
        return _daraja()
    return fake_provider
