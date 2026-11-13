"""Shared objects the routes need, created once per app and stored on app.state."""

from __future__ import annotations

from dataclasses import dataclass

import httpx
from fastapi import HTTPException, Request
from fastapi.templating import Jinja2Templates

from highground.config import Settings
from highground.content import ContentStore, normalize_language
from highground.gauges import GaugeNetwork
from highground.models import Site
from highground.services.summary import SummaryService
from highground.sites import SiteRepository


@dataclass
class AppServices:
    settings: Settings
    content: ContentStore
    sites: SiteRepository
    templates: Jinja2Templates
    summary: SummaryService
    http: httpx.AsyncClient | None = None

    @property
    def gauges(self) -> GaugeNetwork:
        # Re-read each time so edits to gauges.yaml show without a restart.
        return GaugeNetwork.from_config(self.content.gauges())


def get_services(request: Request) -> AppServices:
    return request.app.state.services


def get_language(request: Request) -> str:
    return normalize_language(request.query_params.get("lang") or request.cookies.get("lang"))


def require_site(services: AppServices, site_id: str) -> Site:
    site = services.sites.get(site_id)
    if site is None:
        raise HTTPException(status_code=404, detail=f"Unknown site '{site_id}'")
    return site
