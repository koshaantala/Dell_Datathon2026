"""Latest gauge height from the USGS Water Data OGC API (https://api.waterdata.usgs.gov)."""

from __future__ import annotations

import httpx

from highground.models import GaugeReading

GAUGE_HEIGHT_PARAMETER = "00065"  # gauge height, feet


async def fetch_latest_gauge_height(
    client: httpx.AsyncClient, base_url: str, gauge_id: str
) -> GaugeReading | None:
    """Most recent gauge height, or None if the gauge reports nothing.

    Raises httpx.HTTPError on network or server failure.
    """
    response = await client.get(
        f"{base_url}/collections/latest-continuous/items",
        params={
            "f": "json",
            "monitoring_location_id": gauge_id,
            "parameter_code": GAUGE_HEIGHT_PARAMETER,
        },
    )
    response.raise_for_status()
    features = response.json().get("features", [])
    if not features:
        return None
    props = features[0].get("properties", {})
    try:
        value = float(props["value"])
    except (KeyError, TypeError, ValueError):
        return None
    return GaugeReading(
        gauge_id=gauge_id,
        value=value,
        unit=props.get("unit_of_measure") or "ft",
        time=props.get("time") or "",
    )
