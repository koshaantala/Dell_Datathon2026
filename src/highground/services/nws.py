"""Active National Weather Service alerts for a point (https://www.weather.gov/documentation/services-web-api)."""

from __future__ import annotations

import httpx

from highground.models import Alert


async def fetch_alerts(
    client: httpx.AsyncClient, base_url: str, lat: float, lon: float
) -> list[Alert]:
    """Active alerts covering the point. Raises httpx.HTTPError on failure."""
    response = await client.get(
        f"{base_url}/alerts/active",
        params={"point": f"{lat:.4f},{lon:.4f}"},
        headers={"Accept": "application/geo+json"},
    )
    response.raise_for_status()
    alerts = []
    for feature in response.json().get("features", []):
        props = feature.get("properties", {})
        if not props.get("event"):
            continue
        alerts.append(
            Alert(
                event=props["event"],
                headline=props.get("headline") or "",
                severity=props.get("severity") or "",
                ends=props.get("ends") or props.get("expires"),
            )
        )
    return alerts
