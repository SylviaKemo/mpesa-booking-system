"""
Guards the duplicated price list.

Prices live in app/seed.py and, until the frontend reads the API, also in
frontend/src/data/services.ts. While both exist, a change to one and not the
other would show a client one price and charge another. These tests fail on
that divergence.

Delete this module once the frontend consumes /api/catalogue.
"""

import re
from pathlib import Path

import pytest

from app.seed import ADDITIONS, SETS

_SERVICES_TS = (
    Path(__file__).resolve().parents[2] / "frontend" / "src" / "data" / "services.ts"
)

# Field order differs between tiers and additions in the TypeScript source.
_TIER = re.compile(
    r'id:\s*"(?P<id>[\w-]+)",\s*label:\s*"[^"]+",\s*mins:\s*(?P<mins>\d+),'
    r"\s*amount:\s*(?P<amount>\d+)"
)
_ADDITION = re.compile(
    r'id:\s*"(?P<id>[\w-]+)",\s*label:\s*"[^"]+",\s*amount:\s*(?P<amount>\d+),'
    r"\s*mins:\s*(?P<mins>\d+)"
)


def _frontend_prices() -> dict[str, tuple[int, int]]:
    source = _SERVICES_TS.read_text(encoding="utf-8")
    prices: dict[str, tuple[int, int]] = {}
    for pattern in (_TIER, _ADDITION):
        for match in pattern.finditer(source):
            prices[match["id"]] = (int(match["amount"]), int(match["mins"]))
    return prices


def _backend_prices() -> dict[str, tuple[int, int]]:
    prices = {
        tier["id"]: (tier["amount_kes"], tier["minutes"])
        for lash_set in SETS
        for tier in lash_set["tiers"]
    }
    prices.update(
        {add["id"]: (add["amount_kes"], add["minutes"]) for add in ADDITIONS}
    )
    return prices


@pytest.mark.skipif(
    not _SERVICES_TS.exists(),
    reason="frontend catalogue already removed; this guard is no longer needed",
)
def test_seed_prices_match_the_frontend_catalogue() -> None:
    frontend = _frontend_prices()
    backend = _backend_prices()

    # A regex that silently stops matching would make this test vacuous.
    assert len(frontend) == len(backend) > 0, "parser found no entries"
    assert frontend == backend
