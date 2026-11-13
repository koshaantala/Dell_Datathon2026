"""JSON endpoints used by the page scripts (and handy for testing)."""

from __future__ import annotations

import asyncio
import logging
from typing import Annotated, Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from highground import __version__
from highground.report import band_name, build_report, real_image_path
from highground.services.nws import fetch_alerts
from highground.services.summary import build_facts
from highground.services.usgs import fetch_latest_gauge_height
from highground.web.deps import AppServices, get_language, get_services, require_site

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["api"])

Services = Annotated[AppServices, Depends(get_services)]
Language = Annotated[str, Depends(get_language)]


@router.get("/health")
def health(services: Services) -> dict[str, Any]:
    return {"status": "ok", "version": __version__, "sites": len(services.sites)}


@router.get("/sites")
def sites(services: Services) -> dict[str, Any]:
    return services.sites.to_geojson()


@router.get("/report")
def report(
    services: Services,
    lang: Language,
    site: str | None = None,
    lat: Annotated[float | None, Query(ge=-90, le=90)] = None,
    lon: Annotated[float | None, Query(ge=-180, le=180)] = None,
) -> dict[str, Any]:
    distance_m = 0.0
    if site:
        chosen = require_site(services, site)
    elif lat is not None and lon is not None:
        match = services.sites.nearest(lat, lon, services.settings.max_snap_km)
        if match is None:
            raise HTTPException(status_code=404, detail="Outside coverage")
        chosen, distance_m = match.site, match.distance_m
    else:
        raise HTTPException(status_code=422, detail="Give either site or lat and lon")

    result = build_report(
        chosen, services.content, services.gauges, services.settings.images_dir, lang
    )
    return {
        "site": chosen.model_dump(),
        "distance_m": round(distance_m, 1),
        "score": {
            "points": result.score.points,
            "available": result.score.available,
            "band": result.score.band.model_dump(),
            "factors": [f.model_dump() for f in result.score.factors],
        },
        "gauge": result.gauge.model_dump() if result.gauge else None,
        "upstream_gauge": result.upstream_gauge.model_dump() if result.upstream_gauge else None,
    }


@router.get("/summary")
async def summary(services: Services, lang: Language, site: str) -> dict[str, str]:
    chosen = require_site(services, site)
    result = build_report(chosen, services.content, services.gauges, None, lang)
    facts = build_facts(chosen, result.score, band_name(services.content, result.score, lang))
    text, source = await services.summary.summarize(facts, lang)
    return {"summary": text, "source": source}


@router.get("/live")
async def live(services: Services, site: str) -> dict[str, Any]:
    """Live NWS alerts and the latest gauge height. Each part fails independently."""
    chosen = require_site(services, site)
    settings = services.settings
    if not settings.live_data_enabled or services.http is None:
        return {"enabled": False, "alerts": None, "gauge": None}

    async def alerts() -> list[dict[str, Any]] | None:
        try:
            found = await fetch_alerts(
                services.http, settings.nws_base_url, chosen.latitude, chosen.longitude
            )
        except httpx.HTTPError as exc:
            log.warning("NWS alerts unavailable: %s", exc)
            return None
        return [a.model_dump() for a in found]

    async def gauge() -> dict[str, Any] | None:
        if not chosen.gauge_id:
            return None
        try:
            reading = await fetch_latest_gauge_height(
                services.http, settings.usgs_base_url, chosen.gauge_id
            )
        except httpx.HTTPError as exc:
            log.warning("USGS gauge unavailable: %s", exc)
            return None
        return reading.model_dump() if reading else None

    alert_list, reading = await asyncio.gather(alerts(), gauge())
    return {"enabled": True, "alerts": alert_list, "gauge": reading}


@router.get("/images/{site_id}")
def site_image(services: Services, site_id: str) -> FileResponse:
    chosen = require_site(services, site_id)
    path = real_image_path(services.settings.images_dir, chosen)
    if path is None:
        raise HTTPException(status_code=404, detail="Image not available")
    return FileResponse(path)
