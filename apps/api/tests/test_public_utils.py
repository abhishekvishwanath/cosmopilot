import pytest
from fastapi import HTTPException
from starlette.requests import Request

from app.core.rate_limit import rate_limit
from app.utils.slugify import slugify


def test_slugify_basic() -> None:
    assert slugify("Porcelain Veneers") == "porcelain-veneers"


def test_slugify_strips_punctuation_and_repeats_dashes() -> None:
    assert slugify("Dr. Layla Haddad!!") == "dr-layla-haddad"


def test_slugify_trims_leading_trailing_dashes() -> None:
    assert slugify("  --Teeth Whitening--  ") == "teeth-whitening"


def _make_request(client_host: str = "1.2.3.4") -> Request:
    scope = {
        "type": "http",
        "client": (client_host, 12345),
        "headers": [],
    }
    return Request(scope)


async def test_rate_limit_allows_up_to_max_requests() -> None:
    dependency = rate_limit(max_requests=2, window_seconds=60)
    request = _make_request()

    await dependency(request)
    await dependency(request)


async def test_rate_limit_blocks_after_max_requests() -> None:
    dependency = rate_limit(max_requests=2, window_seconds=60)
    request = _make_request("5.6.7.8")

    await dependency(request)
    await dependency(request)
    with pytest.raises(HTTPException) as exc_info:
        await dependency(request)
    assert exc_info.value.status_code == 429


async def test_rate_limit_tracks_ips_independently() -> None:
    dependency = rate_limit(max_requests=1, window_seconds=60)

    await dependency(_make_request("9.9.9.1"))
    # A different IP has its own bucket — must not be blocked by the first.
    await dependency(_make_request("9.9.9.2"))
