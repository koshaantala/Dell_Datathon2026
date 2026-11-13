"""Live-feed parsers, tested against canned responses (no network)."""

import asyncio

import httpx
import pytest

from highground.services.nws import fetch_alerts
from highground.services.usgs import fetch_latest_gauge_height


def client_returning(payload, status=200):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, json=payload)

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


def test_nws_alerts_are_parsed():
    payload = {
        "features": [
            {
                "properties": {
                    "event": "Flash Flood Warning",
                    "headline": "FFW for Kerr",
                    "severity": "Severe",
                }
            },
            {"properties": {}},
        ]
    }

    async def run():
        async with client_returning(payload) as client:
            return await fetch_alerts(client, "https://nws", 30.0, -99.3)

    alerts = asyncio.run(run())
    assert [a.event for a in alerts] == ["Flash Flood Warning"]


def test_nws_error_raises():
    async def run():
        async with client_returning({}, status=503) as client:
            await fetch_alerts(client, "https://nws", 30.0, -99.3)

    with pytest.raises(httpx.HTTPStatusError):
        asyncio.run(run())


def test_usgs_latest_reading():
    payload = {
        "features": [
            {
                "properties": {
                    "value": "4.12",
                    "unit_of_measure": "ft",
                    "time": "2026-11-13T19:00:00Z",
                }
            }
        ]
    }

    async def run():
        async with client_returning(payload) as client:
            return await fetch_latest_gauge_height(client, "https://usgs", "USGS-08165500")

    reading = asyncio.run(run())
    assert reading.value == 4.12 and reading.unit == "ft"


def test_usgs_no_features_returns_none():
    async def run():
        async with client_returning({"features": []}) as client:
            return await fetch_latest_gauge_height(client, "https://usgs", "USGS-1")

    assert asyncio.run(run()) is None
